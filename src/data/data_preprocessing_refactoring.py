import logging
import os
from pathlib import Path

import click
import duckdb
from dotenv import find_dotenv, load_dotenv

from src.data.utils import configure_s3

logger = logging.getLogger(__name__)


def make_parquet(bucket: str, input_path: str, output_path: str = None) -> str:
    """
    Convert a CSV file stored in S3 into Parquet format using DuckDB.

    Parameters
    ----------
    bucket : str
        Name of the S3 bucket.
    input_path : str
        Path to the CSV file inside the S3 bucket.
    output_path : str, optional
        Destination path for the generated Parquet file.
        If not provided, the function replaces the `.csv` extension
        with `.parquet`.

    Returns
    -------
    str
        The output Parquet file path inside the S3 bucket.
    """
    logger = logging.getLogger(__name__)

    if output_path is None:
        output_path = input_path.replace(".csv", ".parquet")

    con = duckdb.connect(database=":memory:")
    configure_s3(con)

    logger.info(f"Converting s3://{bucket}/{input_path} → s3://{bucket}/{output_path}")

    con.sql(f"""
        COPY (
            SELECT *
            FROM read_csv_auto('s3://{bucket}/{input_path}')
        )
        TO 's3://{bucket}/{output_path}'
        (FORMAT PARQUET)
    """)

    logger.info(f"Parquet saved to s3://{bucket}/{output_path}")
    con.close()
    return output_path


def load_data(path: str) -> duckdb.DuckDBPyRelation:
    """
    Load a Parquet dataset into DuckDB and perform validation checks.

    This function:
    - Loads the dataset into an in-memory DuckDB relation
    - Ensures the dataset is not empty
    - Verifies required columns exist
    - Ensures the main cost column contains valid (non-null) values

    Parameters
    ----------
    path : str
        Local path to the Parquet file.

    Returns
    -------
    duckdb.DuckDBPyRelation
        A DuckDB relation representing the loaded dataset.

    Raises
    ------
    ValueError
        If the dataset is empty, missing required columns,
        or contains only null cost values.
    """
    path = Path(path)

    logger.info(f"Loading data from {path}")
    con = duckdb.connect(":memory:")
    rel = con.sql(f"SELECT * FROM read_parquet('{path}')")

    row_count = rel.aggregate("count(*)").fetchone()[0]
    if row_count == 0:
        logger.error("Parquet file is empty")
        raise ValueError("Parquet is empty")

    cols = rel.columns
    expected_cols = ["country", "year", "region", "cost_vegetables_ppp_usd"]
    missing_cols = [col for col in expected_cols if col not in cols]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        raise ValueError(f"Missing columns: {missing_cols}")

    valid_rows = (
        rel.filter("cost_vegetables_ppp_usd IS NOT NULL")
        .aggregate("count(*)")
        .fetchone()[0]
    )
    if valid_rows == 0:
        logger.error("No valid cost data found")
        raise ValueError("All cost values are NaN")

    logger.info(f"Loaded {row_count:,} rows, {len(cols)} columns")
    return rel


def basic_overview(rel: duckdb.DuckDBPyRelation) -> duckdb.DuckDBPyRelation:
    """
    Generate a compact statistical overview of the dataset.

    The overview includes:
    - Total number of rows
    - Number of unique countries
    - Number of unique regions
    - Number of null values in the vegetable cost column

    Parameters
    ----------
    rel : duckdb.DuckDBPyRelation
        The input DuckDB relation.

    Returns
    -------
    duckdb.DuckDBPyRelation
        A DuckDB relation containing summary statistics.
    """
    return rel.sql(
        f"""
        SELECT 
            count(*) as rows,
            count(DISTINCT country) as unique_countries,
            count(DISTINCT region) as unique_regions,
            sum(CASE WHEN cost_vegetables_ppp_usd IS NULL THEN 1 ELSE 0 END) as null_costs
        FROM {rel}
    """
    )


NUMERIC_COLS = [
    "cost_healthy_diet_ppp_usd",
    "annual_cost_healthy_diet_usd",
    "cost_vegetables_ppp_usd",
    "cost_fruits_ppp_usd",
    "total_food_components_cost",
]


def clean_data(rel: duckdb.DuckDBPyRelation) -> duckdb.DuckDBPyRelation:
    """
    Clean the dataset and engineer new features using SQL transformations.

    This function:
    - Casts numeric fields to proper numeric types
    - Computes aggregated food component costs
    - Derives annual cost from daily PPP cost
    - Computes the annual gap between reported and derived annual costs
    - Calculates year-over-year percentage change
    - Fills missing cost categories

    Parameters
    ----------
    rel : duckdb.DuckDBPyRelation
        The input DuckDB relation.

    Returns
    -------
    duckdb.DuckDBPyRelation
        A new DuckDB relation containing cleaned and enriched data.
    """

    return rel.sql(
        f"""
        SELECT *,
            CAST(cost_healthy_diet_ppp_usd AS DOUBLE) as cost_healthy_diet_ppp_usd,
            CAST(annual_cost_healthy_diet_usd AS DOUBLE) as annual_cost_healthy_diet_usd,
            CAST(year AS INTEGER) as year,

            (COALESCE(cost_vegetables_ppp_usd, 0) + COALESCE(cost_fruits_ppp_usd, 0)) as food_components_sum,
            (cost_healthy_diet_ppp_usd * 365) as annual_from_ppp_usd,
            (annual_cost_healthy_diet_usd - (cost_healthy_diet_ppp_usd * 365)) as annual_gap_usd,

            (cost_healthy_diet_ppp_usd / 
             LAG(cost_healthy_diet_ppp_usd) OVER (PARTITION BY country ORDER BY year) - 1) * 100 as yoy_pct,

            COALESCE(cost_category, 'Unknown') as cost_category

        FROM {rel}
        WHERE cost_healthy_diet_ppp_usd IS NOT NULL
        ORDER BY country, year
    """
    )


def region_consistency_check(rel: duckdb.DuckDBPyRelation) -> duckdb.DuckDBPyRelation:
    """
    Validate that each country is mapped to exactly one region.

    Parameters
    ----------
    rel : duckdb.DuckDBPyRelation
        The input DuckDB relation.

    Returns
    -------
    duckdb.DuckDBPyRelation
        The original relation if validation passes.

    Raises
    ------
    ValueError
        If at least one country is associated with multiple regions.
    """
    logger = logging.getLogger(__name__)

    inconsistent = rel.sql(
        f"""
        SELECT country, count(DISTINCT region) as region_count
        FROM {rel}
        GROUP BY country
        HAVING count(DISTINCT region) > 1
    """
    )

    count_inconsistent = inconsistent.aggregate("count(*)").fetchone()[0]
    if count_inconsistent > 0:
        examples = inconsistent.limit(5).df()
        logger.error(f"Found {count_inconsistent} countries with multiple regions")
        logger.error(f"Examples:\n{examples}")
        raise ValueError(f"{count_inconsistent} countries have inconsistent regions")

    logger.info("All countries have consistent regions")
    return rel


@click.command()
@click.argument("input_filepath", type=click.Path(exists=True), required=False)
@click.argument("output_filepath", type=click.Path(), required=False)
def main(input_filepath, output_filepath):
    """
    Execute the full data processing pipeline.

    The pipeline includes:
    - Optional S3 CSV to Parquet conversion
    - Data loading and validation
    - Region consistency checks
    - Data overview computation
    - Cleaning and feature engineering
    - Export of the processed dataset to Parquet

    Parameters
    ----------
    input_filepath : str
        Path to the input Parquet file.
    output_filepath : str
        Path where the processed Parquet file will be saved.
    """
    load_dotenv()

    logger.info("Starting data processing pipeline")

    MY_BUCKET = os.getenv("MY_BUCKET")
    if MY_BUCKET and os.getenv("CHEMIN_FICHIER"):
        CHEMIN_FICHIER = os.getenv("CHEMIN_FICHIER")
        CHEMIN_PARQUET = os.getenv(
            "CHEMIN_PARQUET", CHEMIN_FICHIER.replace(".csv", ".parquet")
        )
        input_filepath = make_parquet(MY_BUCKET, CHEMIN_FICHIER, CHEMIN_PARQUET)

    rel = load_data(input_filepath)
    rel = region_consistency_check(rel)

    overview = basic_overview(rel).df()
    logger.info(f"Data overview:\n{overview.to_string()}")

    rel_clean = clean_data(rel)

    output_path = Path(output_filepath)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect()
    con.sql(f"COPY ({rel_clean}) TO '{output_path}' (FORMAT PARQUET)")

    row_count = rel_clean.aggregate("count(*)").fetchone()[0]
    logger.info(f"Saved {row_count:,} rows to {output_path}")


if __name__ == "__main__":
    """
    Configure logging and execute the CLI entry point.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    load_dotenv(find_dotenv())
    main()

"""Data loading and preprocessing utilities for the Global Affordability Dashboard.

Handles CSV ingestion, numeric conversion, feature engineering, data quality checks,
and flexible filtering for dashboard exploration.
"""

from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger(__name__)

NUMERIC_COLS: list[str] = [
    "cost_healthy_diet_ppp_usd",
    "annual_cost_healthy_diet_usd",
    "cost_vegetables_ppp_usd",
    "cost_fruits_ppp_usd",
    "total_food_components_cost",
]

EXPECTED_REGIONS: set[str] = {"Africa", "Americas", "Asia", "Europe", "Oceania"}


def load_data(path: str) -> pd.DataFrame:
    """Load and preprocess CSV data with feature engineering and quality checks.

    Performs numeric conversion, derived feature creation, region validation,
    and Year-over-Year percentage change calculation.

    Parameters
    ----------
    path : str
        Path to input CSV file.

    Returns
    -------
    pd.DataFrame
        Preprocessed dataframe ready for dashboard analysis.
    """
    logger.info("Loading data from %s", path)

    df = pd.read_csv(path)
    logger.debug("Raw data loaded: %d rows, %d columns", len(df), len(df.columns))

    # Convert numeric columns
    for col in NUMERIC_COLS + ["year", "country_code"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            logger.debug(
                "Converted %s to numeric (%d non-null)", col, df[col].notna().sum()
            )

    # Clean categorical columns
    df["country"] = df["country"].astype(str).str.strip()
    df["region"] = df["region"].astype(str).str.strip()
    df["cost_category"] = df["cost_category"].fillna("Unknown")
    df["data_quality"] = df["data_quality"].fillna("Unknown")

    # Feature engineering: food components
    df["food_components_sum"] = df[
        ["cost_vegetables_ppp_usd", "cost_fruits_ppp_usd"]
    ].sum(axis=1, min_count=1)

    # Feature engineering: component share
    df["component_share_of_total"] = (
        df["total_food_components_cost"] / df["cost_healthy_diet_ppp_usd"]
    )

    # Sort for YoY calculation
    df = df.sort_values(["country", "year"]).reset_index(drop=True)

    # Year-over-year percentage change
    df["yoy_pct"] = (
        df.groupby("country")["cost_healthy_diet_ppp_usd"].pct_change() * 100
    )
    logger.debug("YoY computed: %d non-null values", df["yoy_pct"].notna().sum())

    # Region cleaning and validation
    df["region_clean"] = df["region"].where(
        df["region"].isin(EXPECTED_REGIONS), "Unknown"
    )

    # Detect countries with inconsistent regions
    country_region_counts = (
        df.groupby("country")["region_clean"]
        .nunique()
        .rename("region_nunique")
        .reset_index()
    )
    df = df.merge(country_region_counts, on="country", how="left")
    df["region_is_suspect"] = df["region_nunique"] > 1

    suspect_countries = df["region_is_suspect"].sum()
    logger.info(
        "Preprocessing complete: %d rows, %d suspect region countries",
        len(df),
        suspect_countries,
    )

    return df


def filter_data(
    df: pd.DataFrame,
    year_range: tuple[int, int],
    regions: list[str],
    categories: list[str],
    qualities: list[str],
    countries: list[str],
    exclude_missing_components: bool,
) -> pd.DataFrame:
    """Apply multi-dimensional filtering to dashboard data.

    Supports year range, region, category, quality, country selection,
    and component completeness filtering.

    Parameters
    ----------
    df : pd.DataFrame
        Preprocessed input dataframe.
    year_range : tuple[int, int]
        Min/max year filter.
    regions : list[str]
        Region filter values.
    categories : list[str]
        Cost category filter values.
    qualities : list[str]
        Data quality filter values.
    countries : list[str]
        Country filter values (optional).
    exclude_missing_components : bool
        Exclude rows missing any component cost data.

    Returns
    -------
    pd.DataFrame
        Filtered dataframe copy.
    """
    logger.debug(
        "Applying filters: years=%s, regions=%d, categories=%d, countries=%d, "
        "exclude_components=%s",
        year_range,
        len(regions),
        len(categories),
        len(countries),
        exclude_missing_components,
    )

    mask = df["year"].between(year_range[0], year_range[1])
    mask &= df["region_clean"].isin(regions)
    mask &= df["cost_category"].isin(categories)
    mask &= df["data_quality"].isin(qualities)

    if countries:
        mask &= df["country"].isin(countries)
        logger.debug("Filtered to %d countries", len(countries))

    if exclude_missing_components:
        component_cols = [
            "cost_vegetables_ppp_usd",
            "cost_fruits_ppp_usd",
            "total_food_components_cost",
        ]
        mask &= df[component_cols].notna().all(axis=1)
        logger.debug("Applied component completeness filter")

    filtered_df = df.loc[mask].copy()
    logger.info(
        "Filtering complete: %d/%d rows retained (%.1f%%)",
        len(filtered_df),
        len(df),
        100 * len(filtered_df) / len(df),
    )

    return filtered_df

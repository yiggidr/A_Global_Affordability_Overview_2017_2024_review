import logging
from typing import List
import duckdb
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(message)s")

NUMERIC_COLS: List[str] = [
    "cost_healthy_diet_ppp_usd",
    "annual_cost_healthy_diet_usd",
    "food_components_sum",
]


def plot_missingness(con: duckdb.DuckDBPyConnection, table: str) -> None:
    """
    Visualize missing values fraction per column using DuckDB.
    """
    logging.info("Calculating missingness per column with DuckDB.")
    query = ", ".join(
        [f"AVG(CASE WHEN {col} IS NULL THEN 1 ELSE 0 END) AS {col}" for col in NUMERIC_COLS]
    )
    missing = con.execute(f"SELECT {query} FROM {table}").df().T
    missing.columns = ["missing_fraction"]
    missing = missing.sort_values("missing_fraction", ascending=False)

    plt.figure(figsize=(10, 4))
    sns.barplot(x=missing.index, y=missing["missing_fraction"], color="#4c72b0")
    plt.xticks(rotation=45, ha="right")
    plt.ylabel("Missing fraction")
    plt.title("Missingness by column")
    plt.tight_layout()
    plt.show()


def summary_statistics(con: duckdb.DuckDBPyConnection, table: str) -> duckdb.DuckDBPyConnection:
    """
    Compute descriptive statistics for numeric columns using DuckDB.
    Returns a DuckDB query result object.
    """
    logging.info("Computing descriptive statistics using DuckDB.")
    stats_query = " UNION ALL ".join(
        [
            f"""
            SELECT
                '{col}' AS column_name,
                MIN({col}) AS min,
                MAX({col}) AS max,
                AVG({col}) AS mean,
                STDDEV_POP({col}) AS std,
                PERCENTILE_CONT({col}, 0.25) AS q1,
                PERCENTILE_CONT({col}, 0.5) AS median,
                PERCENTILE_CONT({col}, 0.75) AS q3
            FROM {table}
            """
            for col in NUMERIC_COLS
        ]
    )
    return con.execute(stats_query)


def plot_distributions(con: duckdb.DuckDBPyConnection, table: str) -> None:
    """
    Plot histograms of key numeric metrics using DuckDB aggregation for counts.
    """
    logging.info("Plotting distributions via DuckDB aggregation.")
    for col, color in zip(NUMERIC_COLS[:2], ["#55a868", "#c44e52"]):
        counts = con.execute(f"""
            SELECT {col}, COUNT(*) AS count
            FROM {table}
            WHERE {col} IS NOT NULL
            GROUP BY {col}
            ORDER BY {col}
        """).df()
        plt.figure(figsize=(6, 4))
        sns.barplot(x=col, y="count", data=counts, color=color)
        plt.title(f"Distribution of {col}")
        plt.show()


def plot_relationships(con: duckdb.DuckDBPyConnection, table: str) -> None:
    """
    Scatter plot and correlation using DuckDB.
    """
    logging.info("Computing correlation via DuckDB.")
    corr_value = con.execute(f"SELECT CORR({NUMERIC_COLS[0]}, {NUMERIC_COLS[1]}) AS corr FROM {table}").fetchone()[0]
    logging.info(f"Correlation between {NUMERIC_COLS[0]} and {NUMERIC_COLS[1]}: {corr_value:.2f}")

    # Scatter plot avec pandas pour seaborn
    df_plot = con.execute(f"SELECT {NUMERIC_COLS[0]}, {NUMERIC_COLS[1]}, cost_category FROM {table}").df()
    plt.figure(figsize=(6, 4))
    sns.scatterplot(data=df_plot, x=NUMERIC_COLS[0], y=NUMERIC_COLS[1], hue="cost_category", alpha=0.6)
    plt.title(f"{NUMERIC_COLS[0]} vs {NUMERIC_COLS[1]} (corr={corr_value:.2f})")
    plt.show()


def plot_trends(con: duckdb.DuckDBPyConnection, table: str) -> None:
    """
    Compute median trends via DuckDB and plot global and regional trends.
    """
    logging.info("Computing median trends using DuckDB.")

    global_trend = con.execute(f"""
        SELECT year, MEDIAN(cost_healthy_diet_ppp_usd) AS median_cost
        FROM {table}
        GROUP BY year
        ORDER BY year
    """).df()

    regional_trend = con.execute(f"""
        SELECT year, region, MEDIAN(cost_healthy_diet_ppp_usd) AS median_cost
        FROM {table}
        GROUP BY year, region
        ORDER BY year
    """).df()

    plt.figure(figsize=(8, 4))
    sns.lineplot(data=global_trend, x="year", y="median_cost", marker="o")
    plt.title("Global median cost (PPP USD)")
    plt.show()

    plt.figure(figsize=(10, 5))
    sns.lineplot(data=regional_trend, x="year", y="median_cost", hue="region", marker="o")
    plt.title("Regional median cost trend (PPP USD)")
    plt.legend(bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.show()


def detect_outliers_iqr(con: duckdb.DuckDBPyConnection, table: str, column: str) -> duckdb.DuckDBPyConnection:
    """
    Detect outliers using IQR in DuckDB. Returns a DuckDB query result object.
    """
    logging.info(f"Detecting outliers in column {column} using DuckDB.")
    q1, q3 = con.execute(f"""
        SELECT PERCENTILE_CONT({column}, 0.25), PERCENTILE_CONT({column}, 0.75)
        FROM {table}
    """).fetchone()
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    return con.execute(f"""
        SELECT * FROM {table}
        WHERE {column} < {lower} OR {column} > {upper}
    """)


def animated_scatter(con: duckdb.DuckDBPyConnection, table: str) -> None:
    """
    Animated scatter plot (DuckDB for size metric calculation).
    """
    logging.info("Preparing animated scatter plot.")
    df_size = con.execute(f"""
        SELECT *, COALESCE(food_components_sum,0) AS size_metric
        FROM {table}
    """).df()

    fig = px.scatter(
        df_size,
        x="cost_healthy_diet_ppp_usd",
        y="annual_cost_healthy_diet_usd",
        color="region",
        size="size_metric",
        hover_name="country",
        animation_frame="year",
        title="PPP vs Annual cost over time",
        size_max=25
    )
    fig.show()


if __name__ == "__main__":
    """
    Exemple d'utilisation :
    1. Connexion à DuckDB et création de table à partir d'un CSV
    2. Appel des fonctions
    """
    con = duckdb.connect("diet.duckdb")
    con.execute("CREATE TABLE IF NOT EXISTS diet AS SELECT * FROM 'dataset.csv'")

    plot_missingness(con, "diet")
    stats = summary_statistics(con, "diet")
    print(stats.df())  # On peut convertir en DataFrame pour affichage rapide
    plot_distributions(con, "diet")
    plot_relationships(con, "diet")
    plot_trends(con, "diet")
    outliers = detect_outliers_iqr(con, "diet", "cost_healthy_diet_ppp_usd")
    print(outliers.df())
    animated_scatter(con, "diet")
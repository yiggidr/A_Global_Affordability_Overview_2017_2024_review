from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

NUMERIC_COLS: list[str] = [
    "cost_healthy_diet_ppp_usd",
    "annual_cost_healthy_diet_usd",
    "cost_vegetables_ppp_usd",
    "cost_fruits_ppp_usd",
    "total_food_components_cost",
    "food_components_sum",
    "component_share_of_total",
    "yoy_pct",
]

DISPLAY_NAMES: dict[str, str] = {
    "country": "Country",
    "year": "Year",
    "region_clean": "Region",
    "cost_category": "Cost category",
    "data_quality": "Data quality",
    "cost_healthy_diet_ppp_usd": "Cost healthy diet PPP USD",
    "annual_cost_healthy_diet_usd": "Annual cost healthy diet USD",
    "cost_vegetables_ppp_usd": "Cost vegetables PPP USD",
    "cost_fruits_ppp_usd": "Cost fruits PPP USD",
    "total_food_components_cost": "Total food components cost",
    "food_components_sum": "Food components sum",
    "component_share_of_total": "Component share of total",
    "yoy_pct": "YoY %",
}

RANKING_DISPLAY_NAMES: dict[str, str] = {
    "country": "Country",
    "first_year": "First year",
    "last_year": "Last year",
    "ppp_first_year": "PPP first year",
    "ppp_last_year": "PPP last year",
    "abs_change": "Absolute change",
    "pct_change": "Percent change",
}


def _fmt(value: float, suffix: str = "") -> str:
    """Format a numeric value for dashboard display.

    Parameters
    ----------
    value : float
        Numeric value to format.
    suffix : str, default=""
        Optional suffix appended to the formatted value.

    Returns
    -------
    str
        Formatted string with two decimal places, or "N/A" for missing values.
    """
    if pd.isna(value):
        return "N/A"
    return f"{value:,.2f}{suffix}"


def compute_kpis(df: pd.DataFrame, metric_col: str, focus_year: int) -> dict[str, Any]:
    """Compute headline KPI values for the selected metric and focus year.

    Parameters
    ----------
    df : pandas.DataFrame
        Filtered input dataframe used by the dashboard.
    metric_col : str
        Name of the metric column to summarize.
    focus_year : int
        Year used for the KPI snapshot.

    Returns
    -------
    dict[str, Any]
        Dictionary containing formatted KPI values for display.
    """
    logger.debug(
        "Computing KPIs for metric=%s and focus_year=%s", metric_col, focus_year
    )

    latest = df[df["year"] == focus_year].copy()
    first_year = int(df["year"].min())
    last_year = int(df["year"].max())

    first_val = df[df["year"] == first_year][metric_col].median()
    last_val = df[df["year"] == last_year][metric_col].median()
    growth = (
        ((last_val - first_val) / first_val * 100)
        if pd.notna(first_val) and first_val != 0
        else np.nan
    )

    est_share = (
        df["data_quality"].eq("Estimated value").mean() * 100 if len(df) else np.nan
    )

    base = latest if not latest.empty else df

    results = {
        "country_count": int(base["country"].nunique()),
        "avg_metric_fmt": _fmt(base[metric_col].mean()),
        "median_metric_fmt": _fmt(base[metric_col].median()),
        "growth_fmt": _fmt(growth, "%"),
        "estimated_share_fmt": _fmt(est_share, "%"),
    }

    logger.debug("KPI computation completed: %s", results)
    return results


def summary_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """Compute descriptive statistics for numeric dashboard variables.

    Parameters
    ----------
    df : pandas.DataFrame
        Input dataframe containing dashboard features.

    Returns
    -------
    pandas.DataFrame
        Summary table with descriptive statistics and human-readable metric names.
    """
    cols = [col for col in NUMERIC_COLS if col in df.columns]
    logger.debug("Computing summary statistics for columns: %s", cols)

    out = df[cols].describe().T.reset_index()

    display_map = {
        "cost_healthy_diet_ppp_usd": "Cost healthy diet PPP USD",
        "annual_cost_healthy_diet_usd": "Annual cost healthy diet USD",
        "cost_vegetables_ppp_usd": "Cost vegetables PPP USD",
        "cost_fruits_ppp_usd": "Cost fruits PPP USD",
        "total_food_components_cost": "Total food components cost",
        "food_components_sum": "Food components sum",
        "component_share_of_total": "Component share of total",
        "yoy_pct": "YoY %",
    }
    out["index"] = out["index"].map(display_map).fillna(out["index"])

    out = out.rename(
        columns={
            "index": "Metric",
            "count": "Count",
            "mean": "Mean",
            "std": "Std Dev",
            "min": "Min",
            "25%": "Q1",
            "50%": "Median",
            "75%": "Q3",
            "max": "Max",
        }
    )

    logger.debug("Summary statistics generated with shape=%s", out.shape)
    return out.round(2)


def yearly_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate yearly summary statistics for the healthy diet PPP metric.

    Parameters
    ----------
    df : pandas.DataFrame
        Input dataframe containing yearly observations.

    Returns
    -------
    pandas.DataFrame
        Year-level summary table with count, mean, median, min, max, and std.
    """
    logger.debug("Computing yearly summary")

    out = (
        df.groupby("year")["cost_healthy_diet_ppp_usd"]
        .agg(["count", "mean", "median", "min", "max", "std"])
        .reset_index()
        .round(2)
    )

    logger.debug("Yearly summary generated with shape=%s", out.shape)
    return out


def top_and_bottom_countries(
    df: pd.DataFrame,
    metric_col: str,
    focus_year: int,
    n: int = 10,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return the highest and lowest ranked countries for a selected year and metric.

    Parameters
    ----------
    df : pandas.DataFrame
        Input dataframe.
    metric_col : str
        Metric used for ranking.
    focus_year : int
        Year used for the ranking.
    n : int, default=10
        Number of countries to return in each ranking.

    Returns
    -------
    tuple[pandas.DataFrame, pandas.DataFrame]
        Top and bottom country ranking tables.
    """
    logger.debug(
        "Computing top and bottom countries for metric=%s, focus_year=%s, n=%s",
        metric_col,
        focus_year,
        n,
    )

    latest = df[df["year"] == focus_year].dropna(subset=[metric_col]).copy()
    country_metric = latest.groupby("country", as_index=False)[metric_col].median()
    top_df = country_metric.nlargest(n, metric_col)
    bottom_df = country_metric.nsmallest(n, metric_col)

    logger.debug(
        "Top/bottom country tables computed with shapes top=%s, bottom=%s",
        top_df.shape,
        bottom_df.shape,
    )
    return top_df, bottom_df


def compute_outliers(df: pd.DataFrame, column: str, focus_year: int) -> pd.DataFrame:
    """Detect outliers for a numeric variable in a given year using the IQR rule.

    Parameters
    ----------
    df : pandas.DataFrame
        Input dataframe.
    column : str
        Numeric column used for outlier detection.
    focus_year : int
        Year used to restrict the analysis.

    Returns
    -------
    pandas.DataFrame
        Sorted outlier table with country, region, and selected metric.
    """
    logger.debug(
        "Computing outliers for column=%s and focus_year=%s", column, focus_year
    )

    tmp = df[df["year"] == focus_year].dropna(subset=[column]).copy()
    if tmp.empty:
        logger.warning(
            "No data available to compute outliers for %s in %s", column, focus_year
        )
        return pd.DataFrame(columns=["country", "region_clean", column])

    q1 = tmp[column].quantile(0.25)
    q3 = tmp[column].quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    outliers = tmp[(tmp[column] < lower) | (tmp[column] > upper)][
        ["country", "region_clean", column]
    ]

    logger.debug("Detected %s outliers for column=%s", len(outliers), column)
    return outliers.sort_values(column, ascending=False).reset_index(drop=True)


def compute_correlation(df: pd.DataFrame) -> pd.DataFrame:
    """Compute the correlation matrix for available numeric dashboard variables.

    Parameters
    ----------
    df : pandas.DataFrame
        Input dataframe.

    Returns
    -------
    pandas.DataFrame
        Rounded Pearson correlation matrix.
    """
    cols = [col for col in NUMERIC_COLS if col in df.columns]
    logger.debug("Computing correlation matrix for columns: %s", cols)

    corr = df[cols].corr(numeric_only=True)

    logger.debug("Correlation matrix generated with shape=%s", corr.shape)
    return corr.round(2)


def build_country_ranking(df: pd.DataFrame) -> pd.DataFrame:
    """Build a country ranking based on first-to-last-year PPP evolution.

    Parameters
    ----------
    df : pandas.DataFrame
        Input dataframe.

    Returns
    -------
    pandas.DataFrame
        Ranking table with first year, last year, absolute change, and percent change.
    """
    logger.debug("Building country ranking")

    tmp = df.dropna(subset=["country", "year", "cost_healthy_diet_ppp_usd"]).copy()

    empty_columns = [
        "country",
        "first_year",
        "last_year",
        "ppp_first_year",
        "ppp_last_year",
        "abs_change",
        "pct_change",
    ]

    if tmp.empty:
        logger.warning("Country ranking could not be computed because input is empty")
        return pd.DataFrame(columns=empty_columns)

    first_year = int(tmp["year"].min())
    last_year = int(tmp["year"].max())

    first = (
        tmp[tmp["year"] == first_year]
        .groupby("country", as_index=False)["cost_healthy_diet_ppp_usd"]
        .median()
        .rename(columns={"cost_healthy_diet_ppp_usd": "ppp_first_year"})
    )

    last = (
        tmp[tmp["year"] == last_year]
        .groupby("country", as_index=False)["cost_healthy_diet_ppp_usd"]
        .median()
        .rename(columns={"cost_healthy_diet_ppp_usd": "ppp_last_year"})
    )

    rank = first.merge(last, on="country", how="inner")

    if rank.empty:
        logger.warning("Country ranking merge returned an empty dataframe")
        return pd.DataFrame(columns=empty_columns)

    rank["first_year"] = first_year
    rank["last_year"] = last_year
    rank["abs_change"] = rank["ppp_last_year"] - rank["ppp_first_year"]
    rank["pct_change"] = (rank["abs_change"] / rank["ppp_first_year"]) * 100

    rank = rank.sort_values("pct_change", ascending=False).round(2)

    logger.debug("Country ranking generated with shape=%s", rank.shape)
    return rank


def generate_insights(
    df: pd.DataFrame,
    metric_col: str,
    metric_label: str,
    focus_year: int,
) -> list[str]:
    """Generate short descriptive insights for the dashboard narrative section.

    Parameters
    ----------
    df : pandas.DataFrame
        Filtered dataframe.
    metric_col : str
        Selected metric column.
    metric_label : str
        Human-readable metric label used in text output.
    focus_year : int
        Selected focus year.

    Returns
    -------
    list[str]
        List of descriptive insights derived from the filtered data.
    """
    logger.debug(
        "Generating insights for metric=%s, metric_label=%s, focus_year=%s",
        metric_col,
        metric_label,
        focus_year,
    )

    insights: list[str] = []

    yearly = df.groupby("year", as_index=False)[metric_col].median()
    if len(yearly) >= 2:
        first_row = yearly.iloc[0]
        last_row = yearly.iloc[-1]
        change = (
            ((last_row[metric_col] - first_row[metric_col]) / first_row[metric_col])
            * 100
            if first_row[metric_col]
            else np.nan
        )
        insights.append(
            f"Median {metric_label.lower()} increased from {first_row[metric_col]:.2f} "
            f"in {int(first_row['year'])} to {last_row[metric_col]:.2f} "
            f"in {int(last_row['year'])}, a change of {change:.1f}%."
        )

    latest = df[df["year"] == focus_year].dropna(subset=[metric_col])
    if not latest.empty:
        top_country = (
            latest.groupby("country")[metric_col]
            .median()
            .sort_values(ascending=False)
            .head(1)
        )
        bottom_country = (
            latest.groupby("country")[metric_col]
            .median()
            .sort_values(ascending=True)
            .head(1)
        )
        if not top_country.empty and not bottom_country.empty:
            insights.append(
                f"In {focus_year}, the highest observed country-level value in the filtered "
                f"data is {top_country.index[0]} ({top_country.iloc[0]:.2f}), while the "
                f"lowest is {bottom_country.index[0]} ({bottom_country.iloc[0]:.2f})."
            )

    yoy = df["yoy_pct"].dropna()
    if not yoy.empty:
        insights.append(
            f"Year-over-year changes show a median of {yoy.median():.2f}% and a standard "
            f"deviation of {yoy.std():.2f}%, indicating non-trivial volatility across "
            f"countries and years."
        )

    est_share = df["data_quality"].eq("Estimated value").mean() * 100
    insights.append(
        f"Estimated values represent {est_share:.1f}% of the filtered rows, so the "
        f"dashboard should be used as descriptive evidence rather than a causal proof engine."
    )

    suspect_share = df["region_is_suspect"].mean() * 100
    if suspect_share > 0:
        insights.append(
            f"About {suspect_share:.1f}% of filtered rows belong to countries with potentially "
            f"inconsistent region assignments, so regional interpretation requires caution."
        )

    logger.debug("Generated %s insights", len(insights))
    return insights

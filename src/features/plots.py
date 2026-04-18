"""Plotting utilities for the Global Affordability Dashboard.

Provides professional visualizations for trends, distributions, correlations,
and categorical breakdowns using Plotly with consistent styling and error handling.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

logger = logging.getLogger(__name__)

PLOT_TEMPLATE: str = "plotly_white"


DISPLAY_NAMES: dict[str, str] = {
    "year": "Year",
    "country": "Country",
    "region": "Region",
    "region_clean": "Region",
    "cost_category": "Cost category",
    "data_quality": "Data quality",
    "region_is_suspect": "Region is suspect",
    "cost_healthy_diet_ppp_usd": "Cost healthy diet PPP USD",
    "annual_cost_healthy_diet_usd": "Annual cost healthy diet USD",
    "cost_vegetables_ppp_usd": "Cost vegetables PPP USD",
    "cost_fruits_ppp_usd": "Cost fruits PPP USD",
    "total_food_components_cost": "Total food components cost",
    "food_components_sum": "Food components sum",
    "annual_from_ppp_usd": "Annual from PPP USD",
    "annual_gap_usd": "Annual gap USD",
    "yoy_pct": "YoY %",
}


def pretty_name(col: str) -> str:
    """Convert technical column name to human-readable display name.

    Parameters
    ----------
    col : str
        Technical column name (snake_case).

    Returns
    -------
    str
        Human-readable display name from DISPLAY_NAMES or title-cased version.
    """
    return DISPLAY_NAMES.get(col, col.replace("_", " ").title())


def plot_global_trend(
    df: pd.DataFrame, metric_col: str, metric_label: str
) -> go.Figure:
    """Plot global trend lines for average and median of selected metric over time.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe with 'year' and metric columns.
    metric_col : str
        Technical name of metric column.
    metric_label : str
        Human-readable metric label for titles/axes.

    Returns
    -------
    plotly.graph_objects.Figure
        Trend plot with average and median lines.
    """
    logger.debug(
        "Plotting global trend for metric=%s with %d rows", metric_col, len(df)
    )

    trend = df.groupby("year", as_index=False).agg(
        avg_metric=(metric_col, "mean"), median_metric=(metric_col, "median")
    )

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=trend["year"],
            y=trend["avg_metric"],
            mode="lines+markers",
            name="Average",
            line=dict(color="#2a9d8f"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=trend["year"],
            y=trend["median_metric"],
            mode="lines+markers",
            name="Median",
            line=dict(color="#e9c46a", dash="dash"),
        )
    )

    fig.update_layout(
        template=PLOT_TEMPLATE,
        title=f"Global trend — {metric_label}",
        xaxis_title=pretty_name("year"),
        yaxis_title=metric_label,
        legend_title_text="Statistic",
        height=500,
        showlegend=True,
    )

    logger.debug("Global trend plot created successfully")
    return fig


def plot_distribution(
    df: pd.DataFrame, metric_col: str, metric_label: str
) -> px.Histogram:
    """Create histogram with box plot marginal for metric distribution.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe with metric column.
    metric_col : str
        Technical name of metric column.
    metric_label : str
        Human-readable metric label.

    Returns
    -------
    plotly.express.Histogram
        Distribution plot with box marginal.
    """
    logger.debug("Creating distribution plot for %s (%d rows)", metric_label, len(df))

    fig = px.histogram(
        df,
        x=metric_col,
        nbins=40,
        marginal="box",
        color_discrete_sequence=["#2a9d8f"],
        template=PLOT_TEMPLATE,
        title=f"Distribution — {metric_label}",
        labels={metric_col: metric_label},
    )
    fig.update_layout(
        xaxis_title=metric_label,
        yaxis_title="Count",
        height=500,
    )

    logger.debug("Distribution plot created successfully")
    return fig


def plot_scatter_relationship(df: pd.DataFrame, year: int | None = None) -> go.Figure:
    """Create scatter plot comparing PPP vs annual healthy diet costs.

    Handles missing data, low sample sizes, and adds jitter for visualization.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe with cost columns.
    year : int, optional
        Filter to specific year.

    Returns
    -------
    plotly.graph_objects.Figure
        PPP vs annual cost scatter plot with appropriate fallbacks.
    """
    logger.info("Creating PPP vs annual cost scatter plot (year=%s)", year)

    tmp = df.copy()
    if year is not None:
        tmp = tmp[tmp["year"] == year].copy()
        logger.debug("Filtered to %d rows for year %s", len(tmp), year)

    # Ensure numeric columns
    tmp["cost_healthy_diet_ppp_usd"] = pd.to_numeric(
        tmp["cost_healthy_diet_ppp_usd"], errors="coerce"
    )
    tmp["annual_cost_healthy_diet_usd"] = pd.to_numeric(
        tmp["annual_cost_healthy_diet_usd"], errors="coerce"
    )
    tmp["cost_category"] = tmp["cost_category"].fillna("Unknown").astype(str)

    # Filter to rows with at least one valid cost
    tmp = tmp[
        tmp["cost_healthy_diet_ppp_usd"].notna()
        | tmp["annual_cost_healthy_diet_usd"].notna()
    ].copy()

    if tmp.empty:
        logger.warning("No data available for scatter plot")
        fig = _empty_figure("No data available with current filters")
        return fig

    tmp_valid = tmp.dropna(
        subset=["cost_healthy_diet_ppp_usd", "annual_cost_healthy_diet_usd"]
    ).copy()

    if tmp_valid.empty:
        logger.warning("No paired PPP/annual data available")
        fig = _empty_figure("No paired PPP and Annual data for this filter")
        return fig

    if len(tmp_valid) < 5:
        logger.warning("Low data count (%d points) for scatter", len(tmp_valid))
        return _low_data_scatter(tmp_valid)

    # Add jitter for better visualization
    rng = np.random.default_rng(42)
    tmp_valid["x_jitter"] = tmp_valid["cost_healthy_diet_ppp_usd"] + rng.normal(
        0, 0.02, len(tmp_valid)
    )
    tmp_valid["y_jitter"] = tmp_valid["annual_cost_healthy_diet_usd"] + rng.normal(
        0, 5, len(tmp_valid)
    )

    fig = px.scatter(
        tmp_valid,
        x="x_jitter",
        y="y_jitter",
        color="cost_category",
        hover_name="country",
        hover_data={
            "year": True,
            "region_clean": True,
            "data_quality": True,
            "cost_healthy_diet_ppp_usd": True,
            "annual_cost_healthy_diet_usd": True,
            "x_jitter": False,
            "y_jitter": False,
        },
        title="PPP vs annual cost",
        template=PLOT_TEMPLATE,
        labels={
            "x_jitter": pretty_name("cost_healthy_diet_ppp_usd"),
            "y_jitter": pretty_name("annual_cost_healthy_diet_usd"),
            "cost_category": pretty_name("cost_category"),
            "country": pretty_name("country"),
            "year": pretty_name("year"),
            "region_clean": pretty_name("region_clean"),
            "data_quality": pretty_name("data_quality"),
        },
    )

    fig.update_traces(
        marker=dict(size=9, opacity=0.75, line=dict(width=0.8, color="white"))
    )
    fig.update_layout(
        xaxis_title=pretty_name("cost_healthy_diet_ppp_usd"),
        yaxis_title=pretty_name("annual_cost_healthy_diet_usd"),
        legend_title_text=pretty_name("cost_category"),
        height=600,
    )

    logger.info("Scatter plot created with %d valid points", len(tmp_valid))
    return fig


def _empty_figure(message: str) -> go.Figure:
    """Create empty figure with centered warning message."""
    fig = px.scatter(title="PPP vs annual cost")
    fig.add_annotation(
        text=message,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font=dict(color="#e76f51", size=14),
    )
    fig.update_layout(template=PLOT_TEMPLATE, height=400)
    return fig


def _low_data_scatter(df: pd.DataFrame) -> px.Scatter:
    """Create scatter plot for low data scenarios (< 5 points)."""
    fig = px.scatter(
        df,
        x="cost_healthy_diet_ppp_usd",
        y="annual_cost_healthy_diet_usd",
        color="cost_category",
        hover_name="country",
        template=PLOT_TEMPLATE,
        title="PPP vs annual cost (low data)",
        labels={
            "cost_healthy_diet_ppp_usd": pretty_name("cost_healthy_diet_ppp_usd"),
            "annual_cost_healthy_diet_usd": pretty_name("annual_cost_healthy_diet_usd"),
            "cost_category": pretty_name("cost_category"),
            "country": pretty_name("country"),
        },
    )
    fig.add_annotation(
        text=f"Only {len(df)} data points",
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font=dict(color="#e76f51", size=14),
    )
    return fig


def plot_correlation_heatmap(corr: pd.DataFrame) -> px.imshow:
    """Create correlation heatmap with human-readable labels.

    Parameters
    ----------
    corr : pd.DataFrame
        Correlation matrix.

    Returns
    -------
    plotly.express.imshow
        Correlation heatmap visualization.
    """
    logger.debug("Creating correlation heatmap (%dx%d)", corr.shape[0], corr.shape[1])

    corr_display = corr.copy()
    corr_display.index = [pretty_name(c) for c in corr_display.index]
    corr_display.columns = [pretty_name(c) for c in corr_display.columns]

    fig = px.imshow(
        corr_display,
        text_auto=True,
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        aspect="auto",
        title="Correlation heatmap",
    )
    fig.update_layout(template=PLOT_TEMPLATE, height=600)

    logger.debug("Correlation heatmap created successfully")
    return fig


def plot_missingness(df: pd.DataFrame) -> px.Bar:
    """Plot missing data fraction by column.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.

    Returns
    -------
    plotly.express.Bar
        Horizontal bar chart of missing fractions.
    """
    logger.debug("Computing missingness for %d rows", len(df))

    missing = df.isna().mean().sort_values(ascending=False).reset_index()
    missing.columns = ["column", "missing_fraction"]
    missing["column"] = missing["column"].map(pretty_name)

    fig = px.bar(
        missing,
        x="column",
        y="missing_fraction",
        title="Missingness by column",
        template=PLOT_TEMPLATE,
        color="missing_fraction",
        color_continuous_scale="Oranges",
        labels={
            "column": "Column",
            "missing_fraction": "Missing fraction",
        },
    )
    fig.update_layout(
        xaxis_title="Column",
        yaxis_title="Missing fraction",
        height=500,
        xaxis_tickangle=45,
    )

    logger.debug("Missingness plot created")
    return fig


def plot_category_distribution(
    df: pd.DataFrame, metric_col: str, metric_label: str, focus_year: int
) -> px.Box:
    """Box plot of metric by cost category for specific year.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.
    metric_col : str
        Metric column name.
    metric_label : str
        Human-readable metric label.
    focus_year : int
        Year to analyze.

    Returns
    -------
    plotly.express.Box
        Box plot by cost category.
    """
    logger.debug(
        "Plotting category distribution for %s in year %d", metric_label, focus_year
    )

    latest = df[df["year"] == focus_year].dropna(subset=[metric_col]).copy()

    fig = px.box(
        latest,
        x="cost_category",
        y=metric_col,
        color="cost_category",
        title=f"Cost category distribution ({focus_year})",
        template=PLOT_TEMPLATE,
        labels={
            "cost_category": pretty_name("cost_category"),
            metric_col: metric_label,
        },
    )
    fig.update_layout(
        xaxis_title=pretty_name("cost_category"),
        yaxis_title=metric_label,
        showlegend=False,
        height=500,
    )

    logger.debug("Category distribution plot created")
    return fig


def plot_top_bottom(
    tmp: pd.DataFrame, metric_col: str, metric_label: str, focus_year: int, mode: str
) -> px.Bar:
    """Horizontal bar chart for top/bottom countries by metric.

    Parameters
    ----------
    tmp : pd.DataFrame
        Country-level data.
    metric_col : str
        Metric column.
    metric_label : str
        Human-readable label.
    focus_year : int
        Analysis year.
    mode : {"top", "bottom"}
        Ranking direction.

    Returns
    -------
    plotly.express.Bar
        Horizontal bar ranking chart.
    """
    logger.debug("Creating %s 10 chart for %s (%d)", mode, metric_label, focus_year)

    title = (
        f"Top 10 countries ({focus_year})"
        if mode == "top"
        else f"Bottom 10 countries ({focus_year})"
    )
    sort_asc = mode == "bottom"

    fig = px.bar(
        tmp.sort_values(metric_col, ascending=sort_asc),
        x=metric_col,
        y="country",
        orientation="h",
        title=title,
        template=PLOT_TEMPLATE,
        color=metric_col,
        color_continuous_scale="Tealgrn",
        labels={
            metric_col: metric_label,
            "country": pretty_name("country"),
        },
    )
    fig.update_layout(
        xaxis_title=metric_label,
        yaxis_title=pretty_name("country"),
        height=600,
    )

    logger.debug("%s chart created", title)
    return fig


def plot_yoy_distribution(df: pd.DataFrame) -> px.Histogram:
    """Histogram of year-over-year percentage changes.

    Parameters
    ----------
    df : pd.DataFrame
        Dataframe with 'yoy_pct' column.

    Returns
    -------
    plotly.express.Histogram
        YoY change distribution.
    """
    logger.debug(
        "Plotting YoY distribution (%d non-null values)", df["yoy_pct"].notna().sum()
    )

    tmp = df.dropna(subset=["yoy_pct"]).copy()

    fig = px.histogram(
        tmp,
        x="yoy_pct",
        nbins=40,
        title="Year-over-year change distribution",
        template=PLOT_TEMPLATE,
        color_discrete_sequence=["#e76f51"],
        labels={"yoy_pct": pretty_name("yoy_pct")},
    )
    fig.update_layout(
        xaxis_title=pretty_name("yoy_pct"),
        yaxis_title="Count",
        height=500,
    )

    logger.debug("YoY distribution plot created")
    return fig


def plot_region_boxplot(
    df: pd.DataFrame, metric_col: str, metric_label: str, focus_year: int
) -> px.Box:
    """Box plot of metric by clean region for specific year.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.
    metric_col : str
        Metric column name.
    metric_label : str
        Human-readable metric label.
    focus_year : int
        Year to analyze.

    Returns
    -------
    plotly.express.Box
        Regional box plot.
    """
    logger.debug("Plotting region boxplot for %s in year %d", metric_label, focus_year)

    latest = df[df["year"] == focus_year].dropna(subset=[metric_col]).copy()

    fig = px.box(
        latest,
        x="region_clean",
        y=metric_col,
        color="region_clean",
        title=f"Regional distribution ({focus_year})",
        template=PLOT_TEMPLATE,
        labels={
            "region_clean": pretty_name("region_clean"),
            metric_col: metric_label,
        },
    )
    fig.update_layout(
        xaxis_title=pretty_name("region_clean"),
        yaxis_title=metric_label,
        showlegend=False,
        height=500,
    )

    logger.debug("Region boxplot created")
    return fig


def plot_component_breakdown(df: pd.DataFrame, focus_year: int) -> go.Figure:
    """Bar chart showing average component costs for specific year.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.
    focus_year : int
        Year to analyze.

    Returns
    -------
    plotly.graph_objects.Figure
        Component cost breakdown or empty figure if no data.
    """
    logger.debug("Plotting component breakdown for year %d", focus_year)

    tmp = df[df["year"] == focus_year].copy()
    component_cols = [
        "cost_vegetables_ppp_usd",
        "cost_fruits_ppp_usd",
        "total_food_components_cost",
    ]

    comp = tmp[component_cols].mean(skipna=True).reset_index()
    comp.columns = ["component", "avg_value"]
    comp = comp.dropna(subset=["avg_value"]).copy()
    comp["component"] = comp["component"].map(pretty_name)

    if comp.empty:
        logger.warning("No component data available for year %d", focus_year)
        fig = go.Figure()
        fig.update_layout(
            template=PLOT_TEMPLATE,
            title=f"No component-cost data available for {focus_year}",
            xaxis_title="Component",
            yaxis_title="Average PPP USD",
            height=400,
            annotations=[
                dict(
                    text="The selected year has no usable component-cost values.",
                    x=0.5,
                    y=0.5,
                    xref="paper",
                    yref="paper",
                    showarrow=False,
                    font=dict(size=14, color="#e76f51"),
                )
            ],
        )
        return fig

    fig = px.bar(
        comp,
        x="component",
        y="avg_value",
        title=f"Average component costs ({focus_year})",
        template=PLOT_TEMPLATE,
        color="component",
        text="avg_value",
        labels={
            "component": "Component",
            "avg_value": "Average PPP USD",
        },
    )

    fig.update_traces(
        texttemplate="%{text:.2f}",
        textposition="outside",
        marker_line_color="white",
        marker_line_width=1,
    )
    fig.update_layout(
        xaxis_title="Component",
        yaxis_title="Average PPP USD",
        showlegend=False,
        yaxis_rangemode="tozero",
        height=500,
    )

    logger.info("Component breakdown created with %d components", len(comp))
    return fig

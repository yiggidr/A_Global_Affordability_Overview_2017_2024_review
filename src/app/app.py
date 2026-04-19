"""Streamlit application for the Global Healthy Diet Dashboard.

This app provides interactive exploration of the cost of a healthy diet
across countries, years, regions, and data-quality segments.
"""

from __future__ import annotations

import logging

import duckdb
import streamlit as st
import streamlit_analytics2 as streamlit_analytics

from app.constants import (
    COMPONENT_FOCUS_YEAR,
    CSS_PATH,
    DATA_PATH,
    RANKING_DISPLAY_NAMES,
)
from app.helpers import pretty_df, read_css_file
from data.db import filter_data, load_data
from features.analysis import (
    build_country_ranking,
    compute_correlation,
    compute_kpis,
    compute_outliers,
    generate_insights,
    summary_statistics,
    top_and_bottom_countries,
    yearly_summary,
)
from features.plots import (
    plot_category_distribution,
    plot_component_breakdown,
    plot_correlation_heatmap,
    plot_distribution,
    plot_global_trend,
    plot_missingness,
    plot_region_boxplot,
    plot_scatter_relationship,
    plot_top_bottom,
    plot_yoy_distribution,
)

logger = logging.getLogger(__name__)


def load_css(file_name: str) -> None:
    """Load a local CSS file and inject it into the Streamlit app.

    Parameters
    ----------
    file_name : str
        Path to the CSS file.

    Returns
    -------
    None
        This function injects CSS into the Streamlit page if the file exists.
    """
    css = read_css_file(file_name)
    if css is not None:
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


@st.cache_data
def get_data():
    """Load and cache the dashboard dataset."""
    logger.info("Loading dashboard data from %s", DATA_PATH)
    return load_data(DATA_PATH)


def render_sidebar(df):
    """Render sidebar filters and return selected values."""
    logger.debug("Rendering sidebar filters")

    st.sidebar.header("Filters")

    min_year = int(df["year"].min())
    max_year = int(df["year"].max())

    year_range = st.sidebar.slider(
        "Year range",
        min_year,
        max_year,
        (min_year, max_year),
    )

    focus_year_options = sorted(df["year"].dropna().unique().tolist())
    focus_year = st.sidebar.selectbox(
        "Focus year",
        options=focus_year_options,
        index=len(focus_year_options) - 1,
    )

    metric_label = st.sidebar.radio(
        "Metric",
        options=["PPP USD / day", "Annual USD"],
        index=0,
    )
    metric_col = {
        "PPP USD / day": "cost_healthy_diet_ppp_usd",
        "Annual USD": "annual_cost_healthy_diet_usd",
    }[metric_label]

    region_options = sorted(df["region_clean"].dropna().unique().tolist())
    selected_regions = st.sidebar.multiselect(
        "Region",
        options=region_options,
        default=region_options,
    )

    category_options = sorted(df["cost_category"].dropna().unique().tolist())
    selected_categories = st.sidebar.multiselect(
        "Cost category",
        options=category_options,
        default=category_options,
    )

    quality_options = sorted(df["data_quality"].dropna().unique().tolist())
    selected_quality = st.sidebar.multiselect(
        "Data quality",
        options=quality_options,
        default=quality_options,
    )

    countries = sorted(df["country"].dropna().unique().tolist())
    selected_countries = st.sidebar.multiselect(
        "Countries (optional)",
        options=countries,
        default=[],
    )

    exclude_missing_components = st.sidebar.checkbox(
        "Exclude rows with missing component costs",
        value=False,
    )
    show_region_warning = st.sidebar.checkbox(
        "Show region quality warning",
        value=True,
    )

    return {
        "min_year": min_year,
        "max_year": max_year,
        "year_range": year_range,
        "focus_year": focus_year,
        "metric_label": metric_label,
        "metric_col": metric_col,
        "selected_regions": selected_regions,
        "selected_categories": selected_categories,
        "selected_quality": selected_quality,
        "selected_countries": selected_countries,
        "exclude_missing_components": exclude_missing_components,
        "show_region_warning": show_region_warning,
    }


def render_kpis(
    filtered_df, metric_col: str, metric_label: str, focus_year: int
) -> None:
    """Render KPI cards for the filtered dataset."""
    logger.debug("Rendering KPI cards")

    kpis = compute_kpis(filtered_df, metric_col, focus_year)
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Countries", f"{kpis['country_count']}")
    col2.metric(f"Average ({metric_label})", kpis["avg_metric_fmt"])
    col3.metric(f"Median ({metric_label})", kpis["median_metric_fmt"])
    col4.metric("Growth first→last", kpis["growth_fmt"])
    col5.metric("Estimated rows", kpis["estimated_share_fmt"])


def render_introduction_tab() -> None:
    """Render the Introduction tab content."""
    st.subheader("Project presentation")
    st.markdown(
        """
This dashboard was developed by **Kwame Mbobda-Kuate, Paco Goze, Youssef Hamzaoui and Avner EL BAZ** as an interactive data application
for exploring the global cost of a healthy diet across countries, years, regions,
and data-quality segments.

The project is based on the Kaggle notebook
**"A Global Affordability Overview (2017–2024)"** by **Hassan Jameel Ahmed**:
https://www.kaggle.com/code/hassanjameelahmed/a-global-affordability-overview-2017-2024/notebook

This Streamlit implementation turns the original exploratory notebook into a more
interactive, reusable, and dashboard-oriented application.
        """
    )

    st.subheader("Project goals")
    st.markdown(
        """
- Understand global cost dynamics of a healthy diet from 2017 to 2024.
- Diagnose data quality issues and quantify missingness.
- Identify trends, outliers, and regional patterns.
- Produce actionable, real-world insights and a dashboard-style overview.
        """
    )

    st.subheader("Key questions")
    st.markdown(
        """
- How has the cost of a healthy diet evolved over time?
- Which countries or regions face the highest costs and the fastest increases?
- Are there visible relationships between cost components and total cost?
- Where are the largest data gaps, and how do they affect interpretation?
        """
    )


def render_overview_tab(
    filtered_df, metric_col: str, metric_label: str, focus_year: int
) -> None:
    """Render the Overview tab content."""
    c1, c2 = st.columns([1.6, 1])
    with c1:
        st.plotly_chart(
            plot_global_trend(filtered_df, metric_col, metric_label),
            use_container_width=True,
        )
    with c2:
        st.plotly_chart(
            plot_distribution(filtered_df, metric_col, metric_label),
            use_container_width=True,
        )

    c3, c4 = st.columns(2)
    with c3:
        st.plotly_chart(
            plot_category_distribution(
                filtered_df, metric_col, metric_label, focus_year
            ),
            use_container_width=True,
        )
    with c4:
        st.plotly_chart(
            plot_region_boxplot(filtered_df, metric_col, metric_label, focus_year),
            use_container_width=True,
        )

    st.subheader("Yearly summary")
    st.dataframe(summary_statistics(filtered_df), use_container_width=True)
    st.dataframe(pretty_df(yearly_summary(filtered_df)), use_container_width=True)


def render_countries_tab(
    filtered_df, metric_col: str, metric_label: str, focus_year: int
) -> None:
    """Render the Countries tab content."""
    c1, c2 = st.columns(2)
    top_df, bottom_df = top_and_bottom_countries(filtered_df, metric_col, focus_year)

    with c1:
        st.plotly_chart(
            plot_top_bottom(top_df, metric_col, metric_label, focus_year, "top"),
            use_container_width=True,
        )
    with c2:
        st.plotly_chart(
            plot_top_bottom(bottom_df, metric_col, metric_label, focus_year, "bottom"),
            use_container_width=True,
        )

    st.subheader("Country ranking")
    ranking_df = build_country_ranking(filtered_df).rename(
        columns=RANKING_DISPLAY_NAMES
    )

    if ranking_df.empty:
        st.info("No country ranking available for the current filters.")
    else:
        st.dataframe(ranking_df, use_container_width=True)


def render_relationships_tab(
    filtered_df,
    metric_col: str,
    focus_year: int,
    min_year: int,
    max_year: int,
) -> None:
    """Render the Relationships tab content."""
    c1, c2 = st.columns(2)
    with c1:
        fig = plot_scatter_relationship(filtered_df, focus_year)
        st.plotly_chart(
            fig,
            use_container_width=True,
            key=f"scatter_{focus_year}_{min_year}_{max_year}",
        )
    with c2:
        corr = compute_correlation(filtered_df)
        st.plotly_chart(plot_correlation_heatmap(corr), use_container_width=True)

    st.subheader("Component breakdown")
    st.caption(
        f"This section is fixed to {COMPONENT_FOCUS_YEAR} because component-level "
        "variables are only usable for that year."
    )
    component_fig = plot_component_breakdown(filtered_df, COMPONENT_FOCUS_YEAR)

    if component_fig is None:
        st.warning(f"No usable component-level data for {COMPONENT_FOCUS_YEAR}.")
    else:
        st.plotly_chart(component_fig, use_container_width=True)


def render_diagnostics_tab(filtered_df, metric_col: str, focus_year: int) -> None:
    """Render the Diagnostics tab content."""
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(plot_missingness(filtered_df), use_container_width=True)
    with c2:
        st.plotly_chart(plot_yoy_distribution(filtered_df), use_container_width=True)

    st.subheader(f"Outliers in {focus_year}")
    outliers = compute_outliers(filtered_df, metric_col, focus_year)
    st.dataframe(pretty_df(outliers), use_container_width=True)


def render_insights_tab(
    filtered_df, metric_col: str, metric_label: str, focus_year: int
) -> None:
    """Render the Insights tab content."""
    insights = generate_insights(filtered_df, metric_col, metric_label, focus_year)
    for item in insights:
        st.markdown(f"- {item}")

    st.subheader("Methodological notes")
    st.markdown(
        """
- The dashboard focuses on descriptive analysis, not causal proof.
- Many rows are marked as estimated values.
- Component-cost variables are more sparsely populated than the main cost variables.
        """
    )


def render_monitoring_tab() -> None:
    """Render the technical monitoring tab using DuckDB logs."""
    st.subheader("Technical Performance Logs")
    st.markdown(
        "This tab displays execution times recorded by the backend monitoring system."
    )

    try:
        with duckdb.connect(DB_PATH, read_only=True) as conn:
            logs_df = conn.execute(
                "SELECT timestamp, function_name, execution_time_seconds, status "
                "FROM performance_logs ORDER BY timestamp DESC LIMIT 100"
            ).df()

            if logs_df.empty:
                st.info("No performance logs available yet.")
            else:
                st.dataframe(logs_df, use_container_width=True)

                st.subheader("Average Execution Time by Function")
                avg_time = conn.execute(
                    "SELECT function_name, AVG(execution_time_seconds) as avg_time "
                    "FROM performance_logs GROUP BY function_name"
                ).df()
                st.bar_chart(avg_time, x="function_name", y="avg_time")

    except Exception as e:
        st.error(f"Could not load monitoring data: {e}")


    Returns
    -------
    None
        Executes the full Streamlit app.
    """
    st.set_page_config(page_title="Healthy Diet Dashboard", layout="wide")

    logger.info("Starting Healthy Diet Dashboard")

    load_css(CSS_PATH)

    st.title("Global Healthy Diet Dashboard")
    st.caption(
        "Interactive dashboard for exploring the cost of a healthy diet across countries, years, and quality segments."
    )

    # Audience tracking
    with streamlit_analytics.track():
        df = get_data()
        filters = render_sidebar(df)

        filtered_df = filter_data(
            df,
            year_range=filters["year_range"],
            regions=filters["selected_regions"],
            categories=filters["selected_categories"],
            qualities=filters["selected_quality"],
            countries=filters["selected_countries"],
            exclude_missing_components=filters["exclude_missing_components"],
        )

        logger.info("Filtered dataset contains %d rows", len(filtered_df))

        if filtered_df.empty:
            logger.warning("No data available after applying filters")
            st.error("No data matches the selected filters.")
            st.stop()

        render_kpis(
            filtered_df,
            filters["metric_col"],
            filters["metric_label"],
            filters["focus_year"],
        )

        tabs = st.tabs(
            [
                "Introduction",
                "Overview",
                "Countries",
                "Relationships",
                "Diagnostics",
                "Insights",
                "Tech Monitoring",
            ]
        )

        with tabs[0]:
            render_introduction_tab()
        with tabs[1]:
            render_overview_tab(
                filtered_df,
                filters["metric_col"],
                filters["metric_label"],
                filters["focus_year"],
            )
        with tabs[2]:
            render_countries_tab(
                filtered_df,
                filters["metric_col"],
                filters["metric_label"],
                filters["focus_year"],
            )
        with tabs[3]:
            render_relationships_tab(
                filtered_df,
                filters["metric_col"],
                filters["focus_year"],
                filters["min_year"],
                filters["max_year"],
            )
        with tabs[4]:
            render_diagnostics_tab(
                filtered_df, filters["metric_col"], filters["focus_year"]
            )
        with tabs[5]:
            render_insights_tab(
                filtered_df,
                filters["metric_col"],
                filters["metric_label"],
                filters["focus_year"],
            )
        with tabs[6]:
            render_monitoring_tab()

    logger.info("Dashboard rendered successfully")


if __name__ == "__main__":
    main()

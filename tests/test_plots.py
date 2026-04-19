"""Pytest unit tests for ``features.plots`` (figures and helpers)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest

from features import plots


@pytest.mark.parametrize(
    ("column", "expected_label"),
    [
        ("year", "Year"),
        ("cost_healthy_diet_ppp_usd", "Cost healthy diet PPP USD"),
        ("unknown_column_xyz", "Unknown Column Xyz"),
    ],
)
def test_pretty_name_mapping_and_fallback(column: str, expected_label: str) -> None:
    """Test pretty name mapping and fallback."""
    assert plots.pretty_name(column) == expected_label


def test_plot_global_trend_returns_figure_with_two_traces() -> None:
    """Test plot global trend returns figure with two traces."""
    df = pd.DataFrame(
        {
            "year": [2019, 2020],
            "cost_healthy_diet_ppp_usd": [2.0, 3.0],
        }
    )
    fig = plots.plot_global_trend(df, "cost_healthy_diet_ppp_usd", "PPP")
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2


def test_plot_distribution_smoke() -> None:
    """Test plot distribution smoke."""
    df = pd.DataFrame({"cost_healthy_diet_ppp_usd": np.random.randn(30) + 3})
    fig = plots.plot_distribution(df, "cost_healthy_diet_ppp_usd", "PPP")
    assert fig.layout.title.text.startswith("Distribution")


def test_plot_scatter_empty_returns_message_figure() -> None:
    """Test plot scatter empty returns message figure."""
    df = pd.DataFrame(
        {
            "year": [2020],
            "country": ["x"],
            "cost_category": ["Low"],
            "region_clean": ["R"],
            "data_quality": ["Official"],
            "cost_healthy_diet_ppp_usd": [np.nan],
            "annual_cost_healthy_diet_usd": [np.nan],
        }
    )
    fig = plots.plot_scatter_relationship(df, year=2020)
    assert isinstance(fig, go.Figure)


def test_plot_correlation_heatmap_smoke() -> None:
    """Test plot correlation heatmap smoke."""
    corr = pd.DataFrame([[1.0, 0.5], [0.5, 1.0]], columns=["a", "b"], index=["a", "b"])
    fig = plots.plot_correlation_heatmap(corr)
    assert fig.layout.title.text == "Correlation heatmap"


def test_plot_component_breakdown_empty_year() -> None:
    """Test plot component breakdown empty year."""
    df = pd.DataFrame(
        {
            "year": [2019],
            "cost_vegetables_ppp_usd": [np.nan],
            "cost_fruits_ppp_usd": [np.nan],
            "total_food_components_cost": [np.nan],
        }
    )
    fig = plots.plot_component_breakdown(df, focus_year=2020)
    assert isinstance(fig, go.Figure)

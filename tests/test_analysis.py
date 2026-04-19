"""Pytest unit tests for ``features.analysis``."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from features import analysis


def test_compute_kpis_basic() -> None:
    """Test basic KPIs computation."""
    df = pd.DataFrame(
        {
            "year": [2020, 2020, 2021, 2021],
            "country": ["a", "b", "a", "b"],
            "cost_healthy_diet_ppp_usd": [2.0, 4.0, 3.0, 5.0],
            "data_quality": ["Official", "Official", "Estimated value", "Official"],
            "region_is_suspect": [False, False, False, False],
        }
    )
    kpis = analysis.compute_kpis(df, "cost_healthy_diet_ppp_usd", focus_year=2021)
    assert kpis["country_count"] == 2
    assert "2.00" in kpis["avg_metric_fmt"] or "4.00" in kpis["avg_metric_fmt"]
    assert "%" in kpis["estimated_share_fmt"]


def test_compute_kpis_growth_when_first_median_zero_uses_nan() -> None:
    """Test growth computation when first median is zero."""
    df = pd.DataFrame(
        {
            "year": [2020, 2021],
            "country": ["x", "x"],
            "cost_healthy_diet_ppp_usd": [0.0, 10.0],
            "data_quality": ["Official", "Official"],
            "region_is_suspect": [False, False],
        }
    )
    kpis = analysis.compute_kpis(df, "cost_healthy_diet_ppp_usd", focus_year=2021)
    assert kpis["growth_fmt"] == "N/A"


def test_summary_statistics_renames_and_rounds() -> None:
    """Test summary statistics renaming and rounding."""
    df = pd.DataFrame(
        {
            "cost_healthy_diet_ppp_usd": [1.0, 2.0],
            "yoy_pct": [np.nan, 5.5],
        }
    )
    out = analysis.summary_statistics(df)
    assert "Metric" in out.columns
    assert "Mean" in out.columns


def test_yearly_summary_groups() -> None:
    """Test yearly summary grouping."""
    df = pd.DataFrame(
        {
            "year": [2019, 2019, 2020],
            "cost_healthy_diet_ppp_usd": [1.0, 3.0, 2.0],
        }
    )
    out = analysis.yearly_summary(df)
    assert len(out) == 2
    assert set(out.columns) >= {"year", "count", "mean", "median", "min", "max", "std"}


def test_top_and_bottom_countries() -> None:
    """Test top and bottom countries computation."""
    df = pd.DataFrame(
        {
            "year": [2021] * 4,
            "country": ["a", "b", "c", "d"],
            "cost_healthy_diet_ppp_usd": [1.0, 2.0, 3.0, 4.0],
        }
    )
    top, bottom = analysis.top_and_bottom_countries(
        df, "cost_healthy_diet_ppp_usd", focus_year=2021, n=2
    )
    assert top["cost_healthy_diet_ppp_usd"].tolist() == [4.0, 3.0]
    assert bottom["cost_healthy_diet_ppp_usd"].tolist() == [1.0, 2.0]


def test_compute_outliers_iqr() -> None:
    """Test compute outliers IQR."""
    # Five points: IQR small enough that 100 is above the upper fence
    df = pd.DataFrame(
        {
            "year": [2020] * 5,
            "country": [f"c{i}" for i in range(5)],
            "region_clean": ["R"] * 5,
            "cost_healthy_diet_ppp_usd": [1.0, 2.0, 3.0, 4.0, 100.0],
        }
    )
    out = analysis.compute_outliers(df, "cost_healthy_diet_ppp_usd", focus_year=2020)
    assert not out.empty
    assert out.iloc[0]["cost_healthy_diet_ppp_usd"] == pytest.approx(100.0)


def test_compute_outliers_empty_year() -> None:
    """Test compute outliers empty year."""
    df = pd.DataFrame(
        {
            "year": [2019],
            "country": ["x"],
            "region_clean": ["R"],
            "cost_healthy_diet_ppp_usd": [np.nan],
        }
    )
    out = analysis.compute_outliers(df, "cost_healthy_diet_ppp_usd", focus_year=2020)
    assert out.empty
    assert list(out.columns) == ["country", "region_clean", "cost_healthy_diet_ppp_usd"]


def test_compute_correlation_subset_of_numeric_cols() -> None:
    """Test compute correlation subset of numeric cols."""
    df = pd.DataFrame(
        {
            "cost_healthy_diet_ppp_usd": [1.0, 2.0, 3.0],
            "cost_vegetables_ppp_usd": [0.1, 0.2, 0.3],
        }
    )
    corr = analysis.compute_correlation(df)
    assert corr.shape[0] == corr.shape[1]
    assert corr.loc["cost_healthy_diet_ppp_usd", "cost_healthy_diet_ppp_usd"] == 1.0


def test_build_country_ranking() -> None:
    """Test build country ranking."""
    df = pd.DataFrame(
        {
            "country": ["a", "a", "b", "b"],
            "year": [2017, 2020, 2017, 2020],
            "cost_healthy_diet_ppp_usd": [10.0, 12.0, 5.0, 6.0],
        }
    )
    rank = analysis.build_country_ranking(df)
    assert not rank.empty
    row_a = rank[rank["country"] == "a"].iloc[0]
    assert row_a["abs_change"] == pytest.approx(2.0)
    assert row_a["pct_change"] == pytest.approx(20.0)


def test_build_country_ranking_empty() -> None:
    """Test build country ranking empty."""
    empty = pd.DataFrame(
        columns=["country", "year", "cost_healthy_diet_ppp_usd"],
    )
    rank = analysis.build_country_ranking(empty)
    assert rank.empty


def test_generate_insights_non_empty(sample_dashboard_df) -> None:
    """Test generate insights non empty."""
    df = sample_dashboard_df
    insights = analysis.generate_insights(
        df,
        metric_col="cost_healthy_diet_ppp_usd",
        metric_label="PPP USD / day",
        focus_year=2017,
    )
    assert isinstance(insights, list)
    assert len(insights) >= 1

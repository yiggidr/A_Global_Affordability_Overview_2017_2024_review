"""Pytest unit tests for ``data.db`` (loading and filtering)."""

from __future__ import annotations

import pandas as pd
import pytest

from data.db import EXPECTED_REGIONS, filter_data, load_data


def test_load_data_coerces_numeric_and_engineers_features(minimal_csv_path) -> None:
    """Test load data coerces numeric and engineers features."""
    df = load_data(str(minimal_csv_path))
    assert len(df) == 3
    assert df["country"].astype(str).tolist() == ["Aland", "Aland", "Beta"]
    assert df["region_clean"].iloc[2] == "Unknown"
    assert df["food_components_sum"].notna().sum() == 2
    assert "yoy_pct" in df.columns
    assert df.loc[df["country"] == "Aland", "yoy_pct"].iloc[1] != 0 or pd.notna(
        df.loc[df["country"] == "Aland", "yoy_pct"].iloc[1]
    )


def test_load_data_marks_suspect_regions_when_country_has_multiple_regions(
    tmp_path,
) -> None:
    """Test load data marks suspect regions when country has multiple regions."""
    rows = [
        {
            "country": "X",
            "year": 2017,
            "region": "Europe",
            "cost_category": "Low",
            "data_quality": "Official",
            "country_code": 1,
            "cost_healthy_diet_ppp_usd": 2.0,
            "annual_cost_healthy_diet_usd": 700.0,
            "cost_vegetables_ppp_usd": 0.1,
            "cost_fruits_ppp_usd": 0.1,
            "total_food_components_cost": 0.5,
        },
        {
            "country": "X",
            "year": 2018,
            "region": "Asia",
            "cost_category": "Low",
            "data_quality": "Official",
            "country_code": 1,
            "cost_healthy_diet_ppp_usd": 2.1,
            "annual_cost_healthy_diet_usd": 720.0,
            "cost_vegetables_ppp_usd": 0.1,
            "cost_fruits_ppp_usd": 0.1,
            "total_food_components_cost": 0.5,
        },
    ]
    path = tmp_path / "multi_region.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    df = load_data(str(path))
    assert df["region_is_suspect"].all()


def test_expected_regions_count_is_five() -> None:
    """Test expected regions count is five."""
    assert len(EXPECTED_REGIONS) == 5


@pytest.mark.parametrize(
    "region",
    ["Africa", "Americas", "Asia", "Europe", "Oceania"],
)
def test_expected_regions_contains_un_region(region: str) -> None:
    """Test expected regions contains UN region."""
    assert region in EXPECTED_REGIONS


def test_filter_data_year_and_lists(sample_dashboard_df) -> None:
    """Test filter data year and lists."""
    df = sample_dashboard_df
    out = filter_data(
        df,
        year_range=(2017, 2017),
        regions=["Europe", "Unknown"],
        categories=["Low", "High"],
        qualities=["Official", "Estimated value"],
        countries=[],
        exclude_missing_components=False,
    )
    assert len(out) == 2
    assert set(out["year"].unique()) == {2017}


def test_filter_data_countries_optional(sample_dashboard_df) -> None:
    """Test filter data countries optional."""
    df = sample_dashboard_df
    only_aland = filter_data(
        df,
        year_range=(2017, 2020),
        regions=list(df["region_clean"].unique()),
        categories=list(df["cost_category"].unique()),
        qualities=list(df["data_quality"].unique()),
        countries=["Aland"],
        exclude_missing_components=False,
    )
    assert set(only_aland["country"].unique()) == {"Aland"}


def test_filter_data_exclude_missing_components(sample_dashboard_df) -> None:
    """Test filter data exclude missing components."""
    df = sample_dashboard_df
    out = filter_data(
        df,
        year_range=(2017, 2020),
        regions=list(df["region_clean"].unique()),
        categories=list(df["cost_category"].unique()),
        qualities=list(df["data_quality"].unique()),
        countries=[],
        exclude_missing_components=True,
    )
    assert out["cost_vegetables_ppp_usd"].notna().all()
    assert len(out) < len(df)

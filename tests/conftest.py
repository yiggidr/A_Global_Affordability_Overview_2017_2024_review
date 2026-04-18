"""Pytest shared fixtures.

The dashboard module ``app.app`` runs ``main()`` at import time and depends on
Streamlit; keep integration-style checks separate and test pure functions in
``data.db`` and ``features`` here.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest


@pytest.fixture
def minimal_csv_path(tmp_path: Path) -> Path:
    """Create a minimal CSV for testing load_data."""
    rows = [
        {
            "country": "Aland",
            "year": 2017,
            "region": "Europe",
            "cost_category": "Low",
            "data_quality": "Official",
            "country_code": 248,
            "cost_healthy_diet_ppp_usd": 3.0,
            "annual_cost_healthy_diet_usd": 1000.0,
            "cost_vegetables_ppp_usd": 0.5,
            "cost_fruits_ppp_usd": 0.3,
            "total_food_components_cost": 1.2,
        },
        {
            "country": "Aland",
            "year": 2018,
            "region": "Europe",
            "cost_category": "Low",
            "data_quality": "Official",
            "country_code": 248,
            "cost_healthy_diet_ppp_usd": 3.3,
            "annual_cost_healthy_diet_usd": 1100.0,
            "cost_vegetables_ppp_usd": 0.6,
            "cost_fruits_ppp_usd": 0.4,
            "total_food_components_cost": 1.3,
        },
        {
            "country": "Beta",
            "year": 2017,
            "region": "NotARegion",
            "cost_category": "High",
            "data_quality": "Estimated value",
            "country_code": 999,
            "cost_healthy_diet_ppp_usd": 5.0,
            "annual_cost_healthy_diet_usd": 2000.0,
            "cost_vegetables_ppp_usd": None,
            "cost_fruits_ppp_usd": None,
            "total_food_components_cost": None,
        },
    ]
    df = pd.DataFrame(rows)
    path = tmp_path / "sample.csv"
    df.to_csv(path, index=False)
    return path


@pytest.fixture
def sample_dashboard_df(minimal_csv_path: Path) -> pd.DataFrame:
    """Preprocessed dataframe as produced by load_data."""
    from data.db import load_data

    return load_data(str(minimal_csv_path))

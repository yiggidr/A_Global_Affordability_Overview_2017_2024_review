"""Tests for ``features.dashboard_presets``."""

from __future__ import annotations

import pandas as pd
import pytest

from features.dashboard_presets import (
    SNAPSHOT_KEYS,
    builtin_presets,
    clamp_snapshot_to_df,
)


@pytest.fixture
def tiny_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "year": [2019, 2020, 2021],
            "country": ["A", "A", "B"],
            "region_clean": ["Europe", "Europe", "Asia"],
            "cost_category": ["Low", "Low", "High"],
            "data_quality": ["Official", "Official", "Estimated value"],
        }
    )


def test_snapshot_keys_match_builtin_full(tiny_df: pd.DataFrame) -> None:
    full = builtin_presets(tiny_df)["All years & categories (max coverage)"]
    assert set(full.keys()) == set(SNAPSHOT_KEYS)


def test_clamp_restores_empty_region_selection(tiny_df: pd.DataFrame) -> None:
    snap = builtin_presets(tiny_df)["All years & categories (max coverage)"].copy()
    snap["selected_regions"] = []
    out = clamp_snapshot_to_df(snap, tiny_df)
    assert len(out["selected_regions"]) > 0


def test_builtin_europe_preset_lists_europe(tiny_df: pd.DataFrame) -> None:
    eu = builtin_presets(tiny_df)["Europe regions only"]
    assert "Europe" in eu["selected_regions"]

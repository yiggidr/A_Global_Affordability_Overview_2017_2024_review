"""Tests for ``app.helpers`` and ``app.constants`` (no Streamlit)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from app.constants import DISPLAY_NAMES
from app.helpers import pretty_df, read_css_file


def test_pretty_df_uses_default_display_names() -> None:
    """Test pretty_df uses default display names."""
    df = pd.DataFrame({"year": [2020], "country": ["X"], "extra": [1]})
    out = pretty_df(df)
    assert "Year" in out.columns
    assert "Country" in out.columns
    assert "extra" in out.columns


def test_pretty_df_accepts_custom_mapping() -> None:
    """Test pretty_df accepts custom mapping."""
    df = pd.DataFrame({"a": [1]})
    out = pretty_df(df, column_map={"a": "Alpha"})
    assert list(out.columns) == ["Alpha"]


@pytest.mark.parametrize(
    "content",
    ["body { color: red; }", ""],
)
def test_read_css_file_reads_existing(tmp_path: Path, content: str) -> None:
    """Test read_css_file reads existing file."""
    path = tmp_path / "theme.css"
    path.write_text(content, encoding="utf-8")
    assert read_css_file(path) == content


def test_read_css_file_missing_returns_none(tmp_path: Path) -> None:
    """Test read_css_file returns None for missing file."""
    assert read_css_file(tmp_path / "missing.css") is None


def test_display_names_covers_core_dashboard_columns() -> None:
    """Test display names covers core dashboard columns."""
    for key in ("year", "country", "cost_healthy_diet_ppp_usd", "yoy_pct"):
        assert key in DISPLAY_NAMES
        label = DISPLAY_NAMES[key]
        assert isinstance(label, str) and label.strip()

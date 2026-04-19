"""Built-in filter presets for the dashboard (pure functions, no Streamlit)."""

from __future__ import annotations

from typing import Any

import pandas as pd

# Keys must match the snapshot dict consumed by the Streamlit app.
SNAPSHOT_KEYS: tuple[str, ...] = (
    "year_range",
    "focus_year",
    "metric_label",
    "selected_regions",
    "selected_categories",
    "selected_quality",
    "selected_countries",
    "exclude_missing_components",
    "show_region_warning",
)


def builtin_presets(df: pd.DataFrame) -> dict[str, dict[str, Any]]:
    """Return preset name → filter snapshot for the given dataframe."""
    min_year = int(df["year"].min())
    max_year = int(df["year"].max())
    region_options = sorted(df["region_clean"].dropna().unique().tolist())
    category_options = sorted(df["cost_category"].dropna().unique().tolist())
    quality_options = sorted(df["data_quality"].dropna().unique().tolist())

    all_regions = region_options
    all_categories = category_options
    all_qualities = quality_options

    full: dict[str, Any] = {
        "year_range": (min_year, max_year),
        "focus_year": max_year,
        "metric_label": "PPP USD / day",
        "selected_regions": list(all_regions),
        "selected_categories": list(all_categories),
        "selected_quality": list(all_qualities),
        "selected_countries": [],
        "exclude_missing_components": False,
        "show_region_warning": True,
    }

    europe_only = ["Europe"] if "Europe" in region_options else (
        [region_options[0]] if region_options else []
    )

    recent_start = max(min_year, min(2020, max_year))
    recent: dict[str, Any] = {
        **full,
        "year_range": (recent_start, max_year),
        "focus_year": max_year,
    }

    official_qualities = [
        q for q in quality_options if "official" in q.lower() or q == "Official"
    ]
    if not official_qualities:
        official_qualities = list(all_qualities)

    official_only: dict[str, Any] = {
        **full,
        "selected_quality": official_qualities,
    }

    presets: dict[str, dict[str, Any]] = {
        "All years & categories (max coverage)": full,
        "2020+ years only": recent,
        "Europe regions only": {
            **full,
            "selected_regions": europe_only,
        },
        "Official / non-estimated quality (if available)": official_only,
    }
    return presets


def clamp_snapshot_to_df(snapshot: dict[str, Any], df: pd.DataFrame) -> dict[str, Any]:
    """Clamp years and lists so they stay valid for ``df``."""
    out = dict(snapshot)
    min_year = int(df["year"].min())
    max_year = int(df["year"].max())
    y0, y1 = out["year_range"]
    y0 = max(min_year, min(int(y0), max_year))
    y1 = max(min_year, min(int(y1), max_year))
    if y0 > y1:
        y0, y1 = min_year, max_year
    out["year_range"] = (y0, y1)

    years_avail = sorted({int(y) for y in df["year"].dropna().unique().tolist()})
    fy = int(out["focus_year"])
    in_span = [y for y in years_avail if y0 <= y <= y1]
    if in_span:
        if fy not in in_span:
            fy = min(in_span, key=lambda x: abs(x - fy))
    elif years_avail:
        fy = years_avail[-1]
    out["focus_year"] = fy

    valid_regions = set(df["region_clean"].dropna().unique())
    out["selected_regions"] = [r for r in out["selected_regions"] if r in valid_regions]
    if not out["selected_regions"]:
        out["selected_regions"] = sorted(valid_regions)

    valid_cat = set(df["cost_category"].dropna().unique())
    out["selected_categories"] = [
        c for c in out["selected_categories"] if c in valid_cat
    ]
    if not out["selected_categories"]:
        out["selected_categories"] = sorted(valid_cat)

    valid_q = set(df["data_quality"].dropna().unique())
    out["selected_quality"] = [q for q in out["selected_quality"] if q in valid_q]
    if not out["selected_quality"]:
        out["selected_quality"] = sorted(valid_q)

    valid_c = set(df["country"].dropna().unique())
    out["selected_countries"] = [c for c in out["selected_countries"] if c in valid_c]

    return out

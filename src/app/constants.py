"""Dashboard constants and display mappings (no Streamlit dependency)."""

from __future__ import annotations

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

RANKING_DISPLAY_NAMES: dict[str, str] = {
    "country": "Country",
    "first_year": "First year",
    "last_year": "Last year",
    "ppp_first_year": "PPP first year",
    "ppp_last_year": "PPP last year",
    "abs_change": "Absolute change",
    "pct_change": "Percent change",
}

DATA_PATH: str = "src/data/price_of_healthy_diet_clean.csv"
CSS_PATH: str = "style.css"
COMPONENT_FOCUS_YEAR: int = 2021

"""Pure, Streamlit-free helpers for the dashboard (safe to import from tests)."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from pathlib import Path

import pandas as pd

from app.constants import DISPLAY_NAMES

logger = logging.getLogger(__name__)


def read_css_file(path: Path | str) -> str | None:
    """Return CSS file contents, or ``None`` if the path does not exist."""
    css_path = Path(path)
    if not css_path.exists():
        logger.warning("CSS file not found: %s", css_path)
        return None
    logger.info("Reading CSS from %s", css_path)
    return css_path.read_text(encoding="utf-8")


def pretty_df(
    df: pd.DataFrame,
    column_map: Mapping[str, str] | None = None,
) -> pd.DataFrame:
    """Rename dataframe columns using dashboard-friendly display names.

    Parameters
    ----------
    df : pandas.DataFrame
        Input dataframe with technical column names.
    column_map : Mapping[str, str], optional
        Column rename mapping. Defaults to :data:`app.constants.DISPLAY_NAMES`.

    Returns
    -------
    pandas.DataFrame
        Dataframe with renamed columns where mappings exist.
    """
    mapping = DISPLAY_NAMES if column_map is None else column_map
    return df.rename(columns=dict(mapping))

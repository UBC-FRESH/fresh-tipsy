"""Column specifications shipped with the package."""

from __future__ import annotations

import csv
import io
from functools import lru_cache
from importlib import resources

from fresh_tipsy.tables.formats import ColumnSpec


@lru_cache(maxsize=2)
def load_columns(table_format: str) -> tuple[ColumnSpec, ...]:
    """Load the column specifications for one table format.

    Parameters
    ----------
    table_format : str
        ``"tab"`` or ``"taf"``.

    Returns
    -------
    tuple of ColumnSpec
        Column specifications in position order.

    Raises
    ------
    ValueError
        When the format is unsupported or the package data has no matching
        rows.
    """
    if table_format not in {"tab", "taf"}:
        message = f"unsupported table format: {table_format!r}"
        raise ValueError(message)
    text = (
        resources.files("fresh_tipsy.tables")
        .joinpath("data/tab-taf-columns.csv")
        .read_text(encoding="utf-8")
    )
    specs = tuple(
        ColumnSpec(
            position=int(row["position"]),
            name=row["name"],
            units=row["units"],
            evidence=row["evidence"],
            confidence=row["confidence"],
        )
        for row in csv.DictReader(io.StringIO(text))
        if row["format"] == table_format
    )
    if not specs:
        message = f"no column specifications for format {table_format!r}"
        raise ValueError(message)
    return specs

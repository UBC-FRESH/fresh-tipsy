"""Growth query models, table selection, and interpolation."""

from __future__ import annotations

from fresh_tipsy.curves.engine import CurveEngine
from fresh_tipsy.curves.errors import (
    InterpolationError,
    ScenarioError,
    SourceUnavailableError,
    UnsupportedQueryError,
)
from fresh_tipsy.curves.interpolation import interpolate_block, interpolate_table, select_block
from fresh_tipsy.curves.models import (
    CurveQuery,
    InterpolatedRow,
    Provenance,
    QueryResult,
    TableSelection,
)

__all__ = [
    "CurveEngine",
    "CurveQuery",
    "InterpolatedRow",
    "InterpolationError",
    "Provenance",
    "QueryResult",
    "ScenarioError",
    "SourceUnavailableError",
    "TableSelection",
    "UnsupportedQueryError",
    "interpolate_block",
    "interpolate_table",
    "select_block",
]

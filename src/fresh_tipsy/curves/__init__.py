"""Growth query models, table selection, interpolation, and metrics."""

from __future__ import annotations

from fresh_tipsy.curves.engine import CurveEngine
from fresh_tipsy.curves.errors import (
    InterpolationError,
    MetricUnavailableError,
    ScenarioError,
    SourceUnavailableError,
    UnknownMetricError,
    UnsupportedQueryError,
)
from fresh_tipsy.curves.interpolation import interpolate_block, interpolate_table, select_block
from fresh_tipsy.curves.metrics import METRICS, MetricSpec, build_curve_point
from fresh_tipsy.curves.models import (
    CurvePoint,
    CurveQuery,
    InterpolatedRow,
    MetricValue,
    Provenance,
    QueryResult,
    TableSelection,
)

__all__ = [
    "METRICS",
    "CurveEngine",
    "CurvePoint",
    "CurveQuery",
    "InterpolatedRow",
    "InterpolationError",
    "MetricSpec",
    "MetricUnavailableError",
    "MetricValue",
    "Provenance",
    "QueryResult",
    "ScenarioError",
    "SourceUnavailableError",
    "TableSelection",
    "UnknownMetricError",
    "UnsupportedQueryError",
    "build_curve_point",
    "interpolate_block",
    "interpolate_table",
    "select_block",
]

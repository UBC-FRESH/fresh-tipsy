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
from fresh_tipsy.curves.validation import MetricComparison, compare_metric

__all__ = [
    "METRICS",
    "CurveEngine",
    "CurvePoint",
    "CurveQuery",
    "InterpolatedRow",
    "InterpolationError",
    "MetricComparison",
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
    "compare_metric",
    "interpolate_block",
    "interpolate_table",
    "select_block",
]

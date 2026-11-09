"""Errors raised by the growth query engine."""

from __future__ import annotations


class UnsupportedQueryError(ValueError):
    """Raised when no source table can answer a growth query."""


class ScenarioError(UnsupportedQueryError):
    """Raised when no run block matches the requested scenario."""


class InterpolationError(UnsupportedQueryError):
    """Raised when an age cannot be interpolated within the source table."""


class SourceUnavailableError(UnsupportedQueryError):
    """Raised when the source table data cannot be loaded."""


class UnknownMetricError(UnsupportedQueryError):
    """Raised when a metric name is not defined."""


class MetricUnavailableError(UnsupportedQueryError):
    """Raised when a metric is not available in the selected source format."""

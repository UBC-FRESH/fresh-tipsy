"""Metric comparison records for validation evidence."""

from __future__ import annotations

import math
from dataclasses import dataclass

from fresh_tipsy.curves.models import MetricValue, Provenance


@dataclass(frozen=True)
class MetricComparison:
    """One query metric compared with an expected value.

    Parameters
    ----------
    metric : str
        Metric name.
    expected : float
        Expected value.
    actual : float
        Query value.
    tolerance : float
        Absolute tolerance.
    passed : bool
        Whether the value is within tolerance.
    age : float
        Query age.
    scenario : str
        Scenario label.
    provenance : Provenance
        Source provenance.
    """

    metric: str
    expected: float
    actual: float
    tolerance: float
    passed: bool
    age: float
    scenario: str
    provenance: Provenance

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-ready comparison record.

        Returns
        -------
        dict of str to object
            Comparison fields.
        """
        return {
            "metric": self.metric,
            "expected": self.expected,
            "actual": self.actual,
            "tolerance": self.tolerance,
            "passed": self.passed,
            "age": self.age,
            "scenario": self.scenario,
            "provenance": self.provenance.as_dict(),
        }


def compare_metric(
    value: MetricValue, expected: float, tolerance: float = 1e-9
) -> MetricComparison:
    """Compare a metric value with an expected value.

    Parameters
    ----------
    value : MetricValue
        Query metric.
    expected : float
        Expected value.
    tolerance : float, optional
        Absolute tolerance. Defaults to ``1e-9``.

    Returns
    -------
    MetricComparison
        Comparison record.

    Raises
    ------
    ValueError
        When the tolerance is negative or either value is not finite.
    """
    if tolerance < 0 or not math.isfinite(tolerance):
        message = "tolerance must be a finite non-negative number"
        raise ValueError(message)
    if not math.isfinite(expected) or not math.isfinite(value.value):
        message = "expected and actual values must be finite"
        raise ValueError(message)
    passed = abs(value.value - expected) <= tolerance
    return MetricComparison(
        metric=value.metric,
        expected=expected,
        actual=value.value,
        tolerance=tolerance,
        passed=passed,
        age=value.age,
        scenario=value.scenario,
        provenance=value.provenance,
    )

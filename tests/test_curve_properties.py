"""Property tests for growth interpolation bounds and monotonicity."""

from __future__ import annotations

from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

from fresh_tipsy.curves import interpolate_block
from fresh_tipsy.tables import parse_tab_file

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "data" / "fixtures" / "synthetic" / "syn0010N02.tab"
BLOCK = parse_tab_file(FIXTURE).blocks[0]

_AGE = st.floats(
    min_value=1.0,
    max_value=3.0,
    allow_nan=False,
    allow_infinity=False,
)


@given(age=_AGE)
def test_interpolation_stays_inside_brackets(age: float) -> None:
    """Interpolated rows stay inside their bracketing ages and values."""
    row = interpolate_block(BLOCK, 0, age)
    assert row.lower_age - 1e-9 <= age <= row.upper_age + 1e-9
    assert 0.0 <= row.fraction <= 1.0
    height = row.values[0]
    assert height is not None
    assert 0.5 <= height <= 1.5


@given(age=st.sampled_from([1.0, 2.0, 3.0]))
def test_exact_age_identity(age: float) -> None:
    """An exact source age returns the source row unchanged."""
    expected = {1.0: 0.5, 2.0: 1.0, 3.0: 1.5}
    row = interpolate_block(BLOCK, 0, age)
    assert row.age == age
    assert row.lower_age == age
    assert row.upper_age == age
    assert row.fraction == 0.0
    assert row.values[0] == expected[age]


@given(a=_AGE, b=_AGE)
def test_height_is_monotonic_between_ages(a: float, b: float) -> None:
    """The synthetic height series is monotonic in age."""
    low, high = sorted((a, b))
    low_row = interpolate_block(BLOCK, 0, low)
    high_row = interpolate_block(BLOCK, 0, high)
    low_height = low_row.values[0]
    high_height = high_row.values[0]
    assert low_height is not None
    assert high_height is not None
    assert low_height <= high_height

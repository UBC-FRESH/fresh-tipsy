"""Property tests for table parsing and normalization invariants."""

from __future__ import annotations

from pathlib import Path

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from fresh_tipsy.tables import normalize_table, parse_tab_file, slugify

_AGES = st.lists(
    st.floats(min_value=0, max_value=500, allow_nan=False, allow_infinity=False),
    min_size=1,
    max_size=5,
    unique=True,
)


def _tab_text(ages: list[float]) -> str:
    """Build a synthetic .tab for a generated age list."""
    header = [
        "[TASS SPECIES]",
        "DatabaseTitle=Synthetic fixture",
        "File=syn0010N02",
        "SpeciesName=Synthetic species",
        "Source=synthetic",
        "Code=SYN",
        "SiteFrom=0",
        "SiteTo=10",
        "TASSsiteIndex=0",
        "TASSsiteSpecies=",
        "PNC=N",
        "PCT=2",
        "",
        "[RUN,1000,0,0]",
        "",
    ]
    rows = ["\t".join([str(age), "1.0", *(["0"] * 20)]) for age in ages]
    return "\n".join([*header, *rows])


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(ages=_AGES)
def test_generated_tab_preserves_row_count_and_range(ages: list[float], tmp_path: Path) -> None:
    """Generated tables parse with the same row count and age range."""
    path = tmp_path / "syn0010N02.tab"
    path.write_text(_tab_text(ages), encoding="ascii")
    table = parse_tab_file(path)
    assert table.data_rows == len(ages)
    assert table.field_count == 22
    assert table.first_age == min(ages)
    assert table.last_age == max(ages)
    normalized = normalize_table(table)
    assert normalized.data_rows == len(ages)
    assert all(len(row.raw) == 22 for row in normalized.rows)


@given(st.text(alphabet="ABCdef 123_-", min_size=1, max_size=30))
def test_slugify_is_stable(value: str) -> None:
    """Slugs are stable, lowercase, and free of spaces."""
    first = slugify(value)
    assert slugify(first) == first
    assert first == first.lower()
    assert " " not in first

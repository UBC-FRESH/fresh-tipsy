"""Fixture self-checks: the synthetic parser fixtures preserve the documented grammar."""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).resolve().parents[1] / "tests" / "data" / "fixtures" / "synthetic"


def _read_lines(name: str) -> list[str]:
    """Read a fixture as ASCII lines without line endings.

    Parameters
    ----------
    name : str
        Fixture filename.

    Returns
    -------
    list of str
        The fixture lines.
    """
    return (FIXTURES / name).read_text(encoding="ascii").splitlines()


def _data_rows(lines: list[str]) -> list[str]:
    """Return the non-empty data rows after the first ``[RUN,...]`` marker.

    Parameters
    ----------
    lines : list of str
        Fixture lines.

    Returns
    -------
    list of str
        Non-empty data lines.
    """
    first = next(index for index, line in enumerate(lines) if line.startswith("[RUN"))
    return [line for line in lines[first + 1 :] if line.strip() and not line.startswith("[RUN")]


def test_fixture_is_marked_synthetic() -> None:
    """The fixture cannot be mistaken for BC source data."""
    lines = _read_lines("syn0010N00.tab")
    assert lines[0] == "[TASS SPECIES]"
    assert "DatabaseTitle=Synthetic fixture - not BC data" in lines
    assert "Source=synthetic" in lines


def test_tab_fixture_keeps_22_fields() -> None:
    """Every non-empty .tab data row has 22 fields."""
    rows = _data_rows(_read_lines("syn0010N00.tab"))
    assert len(rows) == 6
    assert {len(row.split("\t")) for row in rows} == {22}


def test_taf_fixture_keeps_151_fields() -> None:
    """Every non-empty .taf data row has 151 fields."""
    rows = _data_rows(_read_lines("syn0010N00.taf"))
    assert len(rows) == 6
    assert {len(row.split("\t")) for row in rows} == {151}


def test_fixture_contains_a_pct_block() -> None:
    """The fixture has an untreated block and a PCT block."""
    lines = _read_lines("syn0010N00.tab")
    runs = [line for line in lines if line.startswith("[RUN")]
    assert runs == ["[RUN,1000,0,0]", "[RUN,1000,500,0]"]

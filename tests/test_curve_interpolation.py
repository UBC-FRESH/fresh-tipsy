"""Tests for age interpolation and scenario extraction."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from fresh_tipsy.curves import (
    CurveEngine,
    CurveQuery,
    InterpolationError,
    ScenarioError,
    SourceUnavailableError,
    interpolate_block,
)
from fresh_tipsy.tables import (
    TableCatalog,
    build_tab_manifest_entry,
    build_taf_manifest_entry,
    parse_pair,
    parse_tab_file,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "data" / "fixtures" / "synthetic"
FIXTURE_TAB = FIXTURES / "syn0010N02.tab"


def _manifest() -> dict[str, object]:
    """Build a valid synthetic manifest."""
    pair = parse_pair(FIXTURE_TAB)
    return {
        "manifest_version": "1.2.0",
        "generated_at_utc": "2026-11-09T00:00:00Z",
        "extractor": {"name": "fresh-tipsy", "version": "0.1.0", "parser_version": 1},
        "source_install": {"model": "TIPSY", "version": "4.5", "install_env": "TIPSY_INSTALL"},
        "assets": [
            build_tab_manifest_entry(pair.tab, FIXTURES),
            build_taf_manifest_entry(pair.taf, FIXTURES),
        ],
    }


def _engine() -> CurveEngine:
    """Build an engine with the synthetic source root."""
    return CurveEngine(TableCatalog.from_manifest_data(_manifest()), source_root=FIXTURES)


def test_exact_age_returns_source_values() -> None:
    """An exact age returns the source row and bracketing ages."""
    result = _engine().query(CurveQuery("SYN", 5.0, age=2.0))
    assert result.row.age == 2.0
    assert result.row.lower_age == 2.0
    assert result.row.upper_age == 2.0
    assert result.row.fraction == 0.0
    assert result.row.scenario == "untreated"
    assert result.row.values[0] == 1.0
    assert len(result.row.values) == 21


def test_linear_interpolation() -> None:
    """Interpolation is linear between the two source ages."""
    result = _engine().query(CurveQuery("SYN", 5.0, age=2.5))
    assert result.row.lower_age == 2.0
    assert result.row.upper_age == 3.0
    assert result.row.fraction == 0.5
    assert result.row.values[0] == pytest.approx(1.25)


def test_pct_scenario_uses_post_treatment_row() -> None:
    """A PCT query uses the post-treatment duplicate-age row."""
    result = _engine().query(CurveQuery("SYN", 5.0, age=2.0, scenario="PCT"))
    assert result.row.scenario == "PCT"
    assert result.row.block_index == 1
    assert result.row.values[0] == pytest.approx(1.1)


def test_pct_interpolation_uses_post_treatment_series() -> None:
    """Interpolation after treatment uses the post-treatment series."""
    result = _engine().query(CurveQuery("SYN", 5.0, age=1.5, scenario="PCT"))
    assert result.row.lower_age == 1.0
    assert result.row.upper_age == 2.0
    assert result.row.values[0] == pytest.approx(0.8)


def test_density_filter_selects_untreated_or_pct() -> None:
    """Density filters select the matching block."""
    untreated = _engine().query(CurveQuery("SYN", 5.0, age=2.0, initial_density=1000))
    assert untreated.row.scenario == "untreated"
    pct = _engine().query(CurveQuery("SYN", 5.0, age=2.0, pct_density=500))
    assert pct.row.scenario == "PCT"


def test_scenario_and_density_errors() -> None:
    """Missing scenarios and density matches fail explicitly."""
    with pytest.raises(ScenarioError, match="no matching scenario"):
        _engine().query(CurveQuery("SYN", 5.0, age=2.0, scenario="CT"))
    with pytest.raises(ScenarioError, match="no matching scenario"):
        _engine().query(CurveQuery("SYN", 5.0, age=2.0, initial_density=999))
    with pytest.raises(ValueError, match="scenario"):
        CurveQuery("SYN", 5.0, age=2.0, scenario="BURN")


def test_age_bounds_and_missing_age() -> None:
    """Out-of-range and missing ages fail explicitly."""
    with pytest.raises(InterpolationError, match="outside"):
        _engine().query(CurveQuery("SYN", 5.0, age=0.5))
    with pytest.raises(InterpolationError, match="outside"):
        _engine().query(CurveQuery("SYN", 5.0, age=4.0))
    with pytest.raises(InterpolationError, match="age is required"):
        _engine().query(CurveQuery("SYN", 5.0))


def test_source_root_required() -> None:
    """Loading rows without a source root fails explicitly."""
    engine = CurveEngine(TableCatalog.from_manifest_data(_manifest()))
    with pytest.raises(SourceUnavailableError, match="source_root"):
        engine.query(CurveQuery("SYN", 5.0, age=2.0))


def test_taf_interpolation() -> None:
    """The full table interpolates with its own 151-field rows."""
    result = _engine().query(CurveQuery("SYN", 5.0, age=2.0, format="taf"))
    assert result.row.values[0] == 1.0
    assert len(result.row.values) == 150


def test_real_pli_interpolation() -> None:
    """A real PLI query interpolates within its own age grid."""
    database = os.environ.get("TIPSY_DATABASE")
    if database is None:
        pytest.skip("TIPSY_DATABASE is not set")
    root = Path(database)
    pair = parse_pair(root / "pli0530N00.tab")
    manifest: dict[str, object] = {
        "manifest_version": "1.2.0",
        "generated_at_utc": "2026-11-09T00:00:00Z",
        "extractor": {"name": "fresh-tipsy", "version": "0.1.0", "parser_version": 1},
        "source_install": {"model": "TIPSY", "version": "4.5", "install_env": "TIPSY_INSTALL"},
        "assets": [
            build_tab_manifest_entry(pair.tab, root),
            build_taf_manifest_entry(pair.taf, root),
        ],
    }
    engine = CurveEngine(TableCatalog.from_manifest_data(manifest), source_root=root)
    result = engine.query(CurveQuery("PLI", 20.0, age=50.0, pnc="N", stock_height_m=0.13))
    assert result.row.age == 50.0
    assert result.row.lower_age <= 50.0 <= result.row.upper_age
    height = result.row.values[0]
    assert height is not None
    assert height > 0


def test_untreated_scenario_label() -> None:
    """An explicit untreated scenario selects the untreated block."""
    result = _engine().query(CurveQuery("SYN", 5.0, age=2.0, scenario="untreated"))
    assert result.row.scenario == "untreated"
    assert result.row.block_index == 0


def _copy_tab(tmp_path: Path) -> Path:
    """Copy the synthetic tab fixture into a temporary file."""
    path = tmp_path / "syn0010N02.tab"
    path.write_text(FIXTURE_TAB.read_text(encoding="ascii"), encoding="ascii")
    return path


def test_non_numeric_value_raises(tmp_path: Path) -> None:
    """A non-numeric value raises an interpolation error."""
    path = _copy_tab(tmp_path)
    lines = path.read_text(encoding="ascii").splitlines()
    index = next(i for i, line in enumerate(lines) if line.startswith("1\t"))
    fields = lines[index].split("\t")
    fields[1] = "abc"
    lines[index] = "\t".join(fields)
    path.write_text("\n".join(lines), encoding="ascii")
    table = parse_tab_file(path)
    with pytest.raises(InterpolationError, match="not numeric"):
        interpolate_block(table.blocks[0], 0, 1.0)


def test_no_numeric_age_raises(tmp_path: Path) -> None:
    """A block with no numeric age raises an interpolation error."""
    path = _copy_tab(tmp_path)
    lines = path.read_text(encoding="ascii").splitlines()
    for index, line in enumerate(lines):
        if line and line[0].isdigit():
            lines[index] = "\t" + "\t".join(line.split("\t")[1:])
    path.write_text("\n".join(lines), encoding="ascii")
    table = parse_tab_file(path)
    with pytest.raises(InterpolationError, match="no numeric age"):
        interpolate_block(table.blocks[0], 0, 1.0)


def test_blank_value_interpolates_to_none(tmp_path: Path) -> None:
    """A blank endpoint yields a blank interpolated value."""
    path = _copy_tab(tmp_path)
    lines = path.read_text(encoding="ascii").splitlines()
    index = next(i for i, line in enumerate(lines) if line.startswith("2\t"))
    fields = lines[index].split("\t")
    fields[1] = ""
    lines[index] = "\t".join(fields)
    path.write_text("\n".join(lines), encoding="ascii")
    table = parse_tab_file(path)
    row = interpolate_block(table.blocks[0], 0, 1.5)
    assert row.values[0] is None

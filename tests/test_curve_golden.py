"""Golden comparison tests for growth queries."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from fresh_tipsy.curves import (
    CurveEngine,
    CurveQuery,
    MetricComparison,
    compare_metric,
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


def _manifest_for(tab_path: Path, source_root: Path) -> dict[str, object]:
    """Build a manifest for one pair."""
    pair = parse_pair(tab_path)
    return {
        "manifest_version": "1.2.0",
        "generated_at_utc": "2026-11-09T00:00:00Z",
        "extractor": {"name": "fresh-tipsy", "version": "0.1.0", "parser_version": 1},
        "source_install": {"model": "TIPSY", "version": "4.5", "install_env": "TIPSY_INSTALL"},
        "assets": [
            build_tab_manifest_entry(pair.tab, source_root),
            build_taf_manifest_entry(pair.taf, source_root),
        ],
    }


def test_compare_metric_pass_and_fail() -> None:
    """The comparison record marks pass and fail correctly."""
    engine = CurveEngine(
        TableCatalog.from_manifest_data(_manifest_for(FIXTURE_TAB, FIXTURES)),
        source_root=FIXTURES,
    )
    value = engine.metric(CurveQuery("SYN", 5.0, age=2.0), "height_site")
    passed = compare_metric(value, 1.0)
    assert isinstance(passed, MetricComparison)
    assert passed.passed is True
    assert passed.as_dict()["metric"] == "height_site"
    failed = compare_metric(value, 1.0001)
    assert failed.passed is False


def test_compare_metric_rejects_bad_inputs() -> None:
    """Invalid tolerances and non-finite expectations are rejected."""
    engine = CurveEngine(
        TableCatalog.from_manifest_data(_manifest_for(FIXTURE_TAB, FIXTURES)),
        source_root=FIXTURES,
    )
    value = engine.metric(CurveQuery("SYN", 5.0, age=2.0), "height_site")
    with pytest.raises(ValueError, match="tolerance"):
        compare_metric(value, 1.0, tolerance=-1.0)
    with pytest.raises(ValueError, match="finite"):
        compare_metric(value, float("inf"))


def test_real_tipsy_raw_age_golden() -> None:
    """A raw-age query matches the TIPSY row exactly within tolerance."""
    database = os.environ.get("TIPSY_DATABASE")
    if database is None:
        pytest.skip("TIPSY_DATABASE is not set")
    root = Path(database)
    tab_path = root / "pli0530N00.tab"
    engine = CurveEngine(
        TableCatalog.from_manifest_data(_manifest_for(tab_path, root)),
        source_root=root,
    )
    table = parse_tab_file(tab_path)
    row = next(
        row
        for block in table.blocks
        if block.treatment is None
        for row in block.rows
        if row.age == 36.0
    )
    query = CurveQuery("PLI", 20.0, age=36.0, pnc="N", stock_height_m=0.13)
    cases = {
        "volume_gross": float(row.fields[2]),
        "height_top": float(row.fields[19]),
        "stems": float(row.fields[12]),
        "dbh": float(row.fields[9]),
    }
    for metric, expected in cases.items():
        comparison = compare_metric(engine.metric(query, metric), expected)
        assert comparison.passed, comparison.as_dict()


def test_real_tipsy_interpolation_golden() -> None:
    """A midpoint query matches a hand-derived linear interpolation."""
    database = os.environ.get("TIPSY_DATABASE")
    if database is None:
        pytest.skip("TIPSY_DATABASE is not set")
    root = Path(database)
    tab_path = root / "pli0530N00.tab"
    engine = CurveEngine(
        TableCatalog.from_manifest_data(_manifest_for(tab_path, root)),
        source_root=root,
    )
    table = parse_tab_file(tab_path)
    block = next(block for block in table.blocks if block.treatment is None)
    lower = next(row for row in block.rows if row.age == 36.0)
    upper = next(row for row in block.rows if row.age == 41.0)
    midpoint = (36.0 + 41.0) / 2.0
    expected = (float(lower.fields[2]) + float(upper.fields[2])) / 2.0
    query = CurveQuery("PLI", 20.0, age=midpoint, pnc="N", stock_height_m=0.13)
    comparison = compare_metric(engine.metric(query, "volume_gross"), expected, tolerance=1e-6)
    assert comparison.passed, comparison.as_dict()

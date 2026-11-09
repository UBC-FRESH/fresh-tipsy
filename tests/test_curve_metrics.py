"""Tests for typed metric queries."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from fresh_tipsy.curves import (
    CurveEngine,
    CurvePoint,
    CurveQuery,
    MetricUnavailableError,
    MetricValue,
    UnknownMetricError,
)
from fresh_tipsy.tables import (
    TableCatalog,
    build_tab_manifest_entry,
    build_taf_manifest_entry,
    parse_pair,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "data" / "fixtures" / "synthetic"


def _header() -> list[str]:
    """Build a synthetic header for a one-row pair."""
    return [
        "[TASS SPECIES]",
        "DatabaseTitle=Synthetic metrics fixture",
        "File=syn0010N00",
        "SpeciesName=Synthetic species",
        "Source=synthetic",
        "Code=SYN",
        "SiteFrom=0",
        "SiteTo=10",
        "TASSsiteIndex=0",
        "TASSsiteSpecies=",
        "PNC=N",
        "",
        "[RUN,1000,0,0]",
        "",
    ]


def _tab_row() -> list[str]:
    """Build a .tab row with known metric values."""
    fields = ["0"] * 22
    fields[0] = "5"
    fields[1] = "10"
    fields[2] = "100"
    fields[3] = "80"
    fields[4] = "60"
    fields[5] = "40"
    fields[6] = "30"
    fields[9] = "20"
    fields[12] = "1000"
    fields[15] = "55"
    fields[19] = "25"
    fields[20] = "24"
    fields[21] = "26"
    return fields


def _taf_row() -> list[str]:
    """Build a .taf row with known metric values."""
    fields = ["0"] * 151
    fields[0] = "5"
    fields[1] = "10"
    fields[33] = "100"
    fields[34] = "200"
    fields[52] = "50"
    fields[53] = "100"
    fields[79] = "1"
    fields[80] = "2"
    fields[81] = "3"
    fields[82] = "4"
    fields[83] = "5"
    fields[84] = "2"
    fields[85] = "2"
    fields[86] = "2"
    fields[87] = "2"
    fields[88] = "2"
    return fields


def _write_pair(tmp_path: Path) -> Path:
    """Write a synthetic metric pair and return its directory."""
    (tmp_path / "syn0010N00.tab").write_text(
        "\n".join([*_header(), "\t".join(_tab_row())]), encoding="ascii"
    )
    (tmp_path / "syn0010N00.taf").write_text(
        "\n".join([*_header(), "\t".join(_taf_row())]), encoding="ascii"
    )
    return tmp_path


def _engine(tmp_path: Path) -> CurveEngine:
    """Build an engine for the synthetic metric pair."""
    _write_pair(tmp_path)
    pair = parse_pair(tmp_path / "syn0010N00.tab")
    manifest: dict[str, object] = {
        "manifest_version": "1.2.0",
        "generated_at_utc": "2026-11-09T00:00:00Z",
        "extractor": {"name": "fresh-tipsy", "version": "0.1.0", "parser_version": 1},
        "source_install": {"model": "TIPSY", "version": "4.5", "install_env": "TIPSY_INSTALL"},
        "assets": [
            build_tab_manifest_entry(pair.tab, tmp_path),
            build_taf_manifest_entry(pair.taf, tmp_path),
        ],
    }
    return CurveEngine(TableCatalog.from_manifest_data(manifest), source_root=tmp_path)


def test_tab_metrics(tmp_path: Path) -> None:
    """The compact table maps direct growth and density metrics."""
    point = _engine(tmp_path).point(CurveQuery("SYN", 5.0, age=5.0))
    assert isinstance(point, CurvePoint)
    assert point.format == "tab"
    assert point.volume_gross_m3_ha == 100.0
    assert point.volume_total_m3_ha == 80.0
    assert point.volume_merch_m3_ha == 60.0
    assert point.height_site_m == 10.0
    assert point.height_top_m == 25.0
    assert point.height_mean_m == 24.0
    assert point.height_predominant_m == 26.0
    assert point.dbh_cm == 20.0
    assert point.stems_per_ha == 1000.0
    assert point.basal_area_m2_ha == 30.0
    assert point.crown_cover_pct == 55.0
    assert point.biomass_live_odt_ha is None
    assert point.carbon_live_t_ha is None
    assert "biomass_live" in point.unavailable_metrics
    assert "carbon_live" in point.unavailable_metrics


def test_taf_metrics_and_sums(tmp_path: Path) -> None:
    """The full table sums diameter-class and biomass columns."""
    point = _engine(tmp_path).point(CurveQuery("SYN", 5.0, age=5.0, format="taf"))
    assert point.format == "taf"
    assert point.volume_merch_m3_ha == 150.0
    assert point.stems_per_ha == 300.0
    assert point.biomass_live_odt_ha == 15.0
    assert point.biomass_dead_odt_ha == 10.0
    assert point.basal_area_m2_ha == pytest.approx(8.05, abs=0.01)
    assert point.dbh_cm == pytest.approx(18.48, abs=0.02)
    assert point.volume_gross_m3_ha is None
    assert point.height_top_m is None
    assert "height_top" in point.unavailable_metrics
    assert "carbon_live" in point.unavailable_metrics


def test_metric_value_and_evidence(tmp_path: Path) -> None:
    """A named metric returns units and evidence."""
    engine = _engine(tmp_path)
    value = engine.metric(CurveQuery("SYN", 5.0, age=5.0), "volume_gross")
    assert isinstance(value, MetricValue)
    assert value.value == 100.0
    assert value.units == "m³/ha"
    assert value.evidence == "source_table"
    taf_value = engine.metric(CurveQuery("SYN", 5.0, age=5.0, format="taf"), "volume_merch")
    assert taf_value.evidence == "reimplemented"


def test_metric_errors(tmp_path: Path) -> None:
    """Unknown and unavailable metrics fail explicitly."""
    engine = _engine(tmp_path)
    with pytest.raises(UnknownMetricError, match="unknown metric"):
        engine.metric(CurveQuery("SYN", 5.0, age=5.0), "nope")
    with pytest.raises(MetricUnavailableError, match="not available"):
        engine.metric(CurveQuery("SYN", 5.0, age=5.0, format="taf"), "carbon_live")
    with pytest.raises(MetricUnavailableError, match="not available"):
        engine.metric(CurveQuery("SYN", 5.0, age=5.0), "biomass_live")


def test_metric_blank_value(tmp_path: Path) -> None:
    """An available metric with a blank value is reported unavailable."""
    path = tmp_path / "syn0010N00.tab"
    _write_pair(tmp_path)
    lines = path.read_text(encoding="ascii").splitlines()
    fields = lines[-1].split("\t")
    fields[2] = ""
    lines[-1] = "\t".join(fields)
    path.write_text("\n".join(lines), encoding="ascii")
    pair = parse_pair(path)
    manifest: dict[str, object] = {
        "manifest_version": "1.2.0",
        "generated_at_utc": "2026-11-09T00:00:00Z",
        "extractor": {"name": "fresh-tipsy", "version": "0.1.0", "parser_version": 1},
        "source_install": {"model": "TIPSY", "version": "4.5", "install_env": "TIPSY_INSTALL"},
        "assets": [
            build_tab_manifest_entry(pair.tab, tmp_path),
            build_taf_manifest_entry(pair.taf, tmp_path),
        ],
    }
    engine = CurveEngine(TableCatalog.from_manifest_data(manifest), source_root=tmp_path)
    with pytest.raises(MetricUnavailableError, match="no value"):
        engine.metric(CurveQuery("SYN", 5.0, age=5.0), "volume_gross")


def test_real_pli_metrics() -> None:
    """A real PLI query returns a positive volume metric."""
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
    value = engine.metric(
        CurveQuery("PLI", 20.0, age=50.0, pnc="N", stock_height_m=0.13),
        "volume_gross",
    )
    assert value.value > 0
    assert value.evidence == "source_table"

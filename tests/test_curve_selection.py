"""Tests for catalog-based growth table selection."""

from __future__ import annotations

import copy
import json
import math
import os
from dataclasses import replace
from pathlib import Path

import pytest

from fresh_tipsy.curves import (
    CurveEngine,
    CurveQuery,
    Provenance,
    SourceUnavailableError,
    TableSelection,
    UnsupportedQueryError,
)
from fresh_tipsy.tables import (
    TableCatalog,
    build_tab_manifest_entry,
    build_taf_manifest_entry,
    parse_pair,
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


def _engine(manifest: dict[str, object] | None = None) -> CurveEngine:
    """Build an engine from a manifest."""
    return CurveEngine(TableCatalog.from_manifest_data(manifest or _manifest()))


def _asset(manifest: dict[str, object]) -> dict[str, object]:
    """Return the first asset mapping."""
    assets = manifest["assets"]
    assert isinstance(assets, list)
    asset = assets[0]
    assert isinstance(asset, dict)
    return asset


def _add_variant(
    manifest: dict[str, object],
    *,
    asset_id: str,
    pnc: str,
    stock_height: float | None,
) -> None:
    """Append a catalog variant of the first table asset."""
    assets = manifest["assets"]
    assert isinstance(assets, list)
    variant = copy.deepcopy(_asset(manifest))
    variant["id"] = asset_id
    metadata = variant["metadata"]
    assert isinstance(metadata, dict)
    metadata["pnc"] = pnc
    if stock_height is None:
        metadata.pop("stock_height_m", None)
    else:
        metadata["stock_height_m"] = stock_height
    assets.append(variant)


def test_selects_compact_table() -> None:
    """A supported query selects the compact table with provenance."""
    selection = _engine().select_table(CurveQuery("SYN", 5.0))
    assert isinstance(selection, TableSelection)
    assert selection.entry.asset_id == "tipsy45-db-syn0010n02-tab"
    assert selection.provenance.asset_id == selection.entry.asset_id
    assert len(selection.provenance.sha256) == 64
    assert selection.provenance.evidence == "source_table"
    assert "default PNC N" in selection.rationale


def test_selects_full_table() -> None:
    """The format filter selects the full table."""
    selection = _engine().select_table(CurveQuery("SYN", 5.0, format="taf"))
    assert selection.entry.asset_id == "tipsy45-db-syn0010n02-taf"
    assert selection.provenance.format == "taf"


def test_unknown_species() -> None:
    """An unknown species fails explicitly."""
    with pytest.raises(UnsupportedQueryError, match="unknown species"):
        _engine().select_table(CurveQuery("PLI", 20.0))


def test_site_outside_range() -> None:
    """A site outside every range fails explicitly."""
    with pytest.raises(UnsupportedQueryError, match="site index"):
        _engine().select_table(CurveQuery("SYN", 20.0))


def test_pnc_mismatch() -> None:
    """An unsupported PNC fails explicitly."""
    with pytest.raises(UnsupportedQueryError, match="PNC"):
        _engine().select_table(CurveQuery("SYN", 5.0, pnc="C"))


def test_stock_height_mismatch() -> None:
    """An unsupported stock height fails explicitly."""
    with pytest.raises(UnsupportedQueryError, match="stock height"):
        _engine().select_table(CurveQuery("SYN", 5.0, stock_height_m=0.13))


def test_source_version_mismatch() -> None:
    """An unsupported source version fails explicitly."""
    with pytest.raises(UnsupportedQueryError, match="source version"):
        _engine().select_table(CurveQuery("SYN", 5.0, source_version="9.9"))


def test_query_validation() -> None:
    """Invalid query fields raise ValueError."""
    with pytest.raises(ValueError, match="species_code"):
        CurveQuery(" ", 5.0)
    with pytest.raises(ValueError, match="site_index"):
        CurveQuery("SYN", math.nan)
    with pytest.raises(ValueError, match="age"):
        CurveQuery("SYN", 5.0, age=-1)
    with pytest.raises(ValueError, match="stock_height_m"):
        CurveQuery("SYN", 5.0, stock_height_m=-1)
    with pytest.raises(ValueError, match="pnc"):
        CurveQuery("SYN", 5.0, pnc="X")
    with pytest.raises(ValueError, match="format"):
        CurveQuery("SYN", 5.0, format="csv")


def test_pnc_and_stock_height_policy() -> None:
    """The selection rule prefers N, then an unspecified height, then the smallest."""
    manifest = _manifest()
    _add_variant(manifest, asset_id="tipsy45-db-syn0010n02-tab-n013", pnc="N", stock_height=0.13)
    _add_variant(manifest, asset_id="tipsy45-db-syn0010n02-tab-n021", pnc="N", stock_height=0.21)
    _add_variant(manifest, asset_id="tipsy45-db-syn0010n02-tab-c-none", pnc="C", stock_height=None)
    _add_variant(manifest, asset_id="tipsy45-db-syn0010n02-tab-p-none", pnc="P", stock_height=None)
    engine = _engine(manifest)
    default = engine.select_table(CurveQuery("SYN", 5.0))
    assert default.entry.asset_id == "tipsy45-db-syn0010n02-tab"
    assert "default PNC N" in default.rationale
    assert "default stock height unspecified" in default.rationale
    c_table = engine.select_table(CurveQuery("SYN", 5.0, pnc="C"))
    assert c_table.entry.asset_id == "tipsy45-db-syn0010n02-tab-c-none"
    tall = engine.select_table(CurveQuery("SYN", 5.0, stock_height_m=0.21))
    assert tall.entry.asset_id == "tipsy45-db-syn0010n02-tab-n021"


def test_from_manifest(tmp_path: Path) -> None:
    """An engine loads a manifest file."""
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(_manifest()), encoding="utf-8")
    selection = CurveEngine.from_manifest(path).select_table(CurveQuery("SYN", 5.0))
    assert selection.entry.asset_id == "tipsy45-db-syn0010n02-tab"


def test_provenance_as_dict() -> None:
    """Provenance converts to a JSON-ready mapping."""
    provenance = Provenance.from_entry(_engine().select_table(CurveQuery("SYN", 5.0)).entry)
    data = provenance.as_dict()
    assert data["sha256"] == provenance.sha256
    assert data["source_model"] == "TIPSY"


def test_real_pli_selection() -> None:
    """A real PLI pair selects with stock height when TIPSY_DATABASE is set."""
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
    selection = _engine(manifest).select_table(
        CurveQuery("PLI", 20.0, pnc="N", stock_height_m=0.13)
    )
    assert selection.entry.asset_id == "tipsy45-db-pli0530n00-tab"
    assert selection.provenance.relative_path == "pli0530N00.tab"


def test_default_smallest_stock_height() -> None:
    """When every candidate has a height, the smallest is the default."""
    manifest = _manifest()
    assets = manifest["assets"]
    assert isinstance(assets, list)
    base = _asset(manifest)
    assets.clear()
    for asset_id, height in (
        ("tipsy45-db-syn0010n02-tab-h013", 0.13),
        ("tipsy45-db-syn0010n02-tab-h021", 0.21),
    ):
        variant = copy.deepcopy(base)
        variant["id"] = asset_id
        metadata = variant["metadata"]
        assert isinstance(metadata, dict)
        metadata["stock_height_m"] = height
        assets.append(variant)
    selection = _engine(manifest).select_table(CurveQuery("SYN", 5.0))
    assert selection.entry.asset_id == "tipsy45-db-syn0010n02-tab-h013"
    assert "default stock height 0.13" in selection.rationale


def test_default_latest_source_version() -> None:
    """When versions differ, the latest is the default."""
    manifest = _manifest()
    base = _asset(manifest)
    newer = copy.deepcopy(base)
    newer["id"] = "tipsy45-db-syn0010n02-tab-new"
    source = newer["source"]
    assert isinstance(source, dict)
    source["version"] = "4.6"
    assets = manifest["assets"]
    assert isinstance(assets, list)
    assets.append(newer)
    selection = _engine(manifest).select_table(CurveQuery("SYN", 5.0))
    assert selection.entry.source_version == "4.6"
    assert "default source version 4.6" in selection.rationale


def test_missing_format() -> None:
    """A requested format with no candidate fails explicitly."""
    manifest = _manifest()
    assets = manifest["assets"]
    assert isinstance(assets, list)
    assets[:] = [asset for asset in assets if asset.get("format") != "taf"]
    with pytest.raises(UnsupportedQueryError, match="no taf table"):
        _engine(manifest).select_table(CurveQuery("SYN", 5.0, format="taf"))


def test_load_table_missing_file(tmp_path: Path) -> None:
    """A missing source file raises a source error."""
    engine = CurveEngine(TableCatalog.from_manifest_data(_manifest()), source_root=tmp_path)
    selection = engine.select_table(CurveQuery("SYN", 5.0))
    with pytest.raises(SourceUnavailableError, match="cannot be read"):
        engine.load_table(selection)


def test_load_table_path_escape() -> None:
    """A source path outside the root raises a source error."""
    engine = CurveEngine(TableCatalog.from_manifest_data(_manifest()), source_root=FIXTURES)
    selection = engine.select_table(CurveQuery("SYN", 5.0))
    escaped = replace(
        selection,
        provenance=replace(selection.provenance, relative_path="../outside.tab"),
    )
    with pytest.raises(SourceUnavailableError, match="escapes"):
        engine.load_table(escaped)

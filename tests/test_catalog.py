"""Tests for the table catalog and search index."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from fresh_tipsy.tables import (
    CatalogError,
    CatalogQuery,
    TableCatalog,
    build_tab_manifest_entry,
    build_taf_manifest_entry,
    load_columns,
    parse_pair,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "data" / "fixtures" / "synthetic"
FIXTURE_TAB = FIXTURES / "syn0010N02.tab"
EXAMPLE_MANIFEST = ROOT / "notes" / "reference" / "manifest-example.json"
REFERENCE_COLUMNS = ROOT / "notes" / "reference" / "tab-taf-columns.csv"


def _manifest_data() -> dict[str, object]:
    """Build a synthetic manifest with one .tab/.taf pair."""
    pair = parse_pair(FIXTURE_TAB)
    return {
        "manifest_version": "1.1.0",
        "generated_at_utc": "2026-11-09T00:00:00Z",
        "extractor": {"name": "fresh-tipsy", "version": "0.1.0", "parser_version": 1},
        "source_install": {"model": "TIPSY", "version": "4.5", "install_env": "TIPSY_INSTALL"},
        "assets": [
            build_tab_manifest_entry(pair.tab, FIXTURES),
            build_taf_manifest_entry(pair.taf, FIXTURES),
        ],
    }


def test_catalog_loads_and_gets_entries() -> None:
    """The catalog loads both formats and returns an entry by ID."""
    catalog = TableCatalog.from_manifest_data(_manifest_data())
    assert len(catalog) == 2
    assert {entry.format for entry in catalog.entries} == {"tab", "taf"}
    entry = catalog.get("tipsy45-db-syn0010n02-tab")
    assert entry is not None
    assert entry.species_code == "SYN"
    assert entry.column_count == 22
    assert len(entry.columns) == 22


def test_catalog_filters() -> None:
    """Species, site, PNC, format, source, and text filters compose."""
    catalog = TableCatalog.from_manifest_data(_manifest_data())
    results = catalog.search(
        CatalogQuery(
            species_code="syn",
            site_index=5.0,
            pnc="n",
            source_version="4.5",
            format="tab",
            text="synthetic",
        )
    )
    assert len(results) == 1
    assert results[0].asset_id == "tipsy45-db-syn0010n02-tab"
    assert catalog.search(CatalogQuery(site_index=20.0)) == ()
    assert catalog.search(CatalogQuery(pnc="C")) == ()
    assert catalog.search(CatalogQuery(format="taf"))[0].field_count == 151


def test_catalog_entry_as_dict() -> None:
    """The JSON-ready entry expands columns and keeps provenance."""
    catalog = TableCatalog.from_manifest_data(_manifest_data())
    taf = catalog.get("tipsy45-db-syn0010n02-taf")
    assert taf is not None
    data = taf.as_dict()
    assert data["format"] == "taf"
    assert data["column_count"] == 151
    columns = data["columns"]
    assert isinstance(columns, list)
    assert len(columns) == 151


def test_catalog_loads_manifest_example() -> None:
    """The committed 1.1.0 manifest example loads with its metadata."""
    catalog = TableCatalog.from_manifest(EXAMPLE_MANIFEST)
    assert len(catalog) == 2
    results = catalog.search(
        CatalogQuery(
            species_code="PLI",
            site_index=20.0,
            pnc="N",
            stock_height_m=0.13,
            format="tab",
        )
    )
    assert len(results) == 1
    assert results[0].asset_id == "tipsy45-db-pli0530n00-tab"


def test_catalog_rejects_missing_metadata() -> None:
    """A tipsy_table without metadata is a catalog error."""
    data = _manifest_data()
    assets = data["assets"]
    assert isinstance(assets, list)
    first = assets[0]
    assert isinstance(first, dict)
    first.pop("metadata")
    with pytest.raises(CatalogError, match="metadata"):
        TableCatalog.from_manifest_data(data)


def test_catalog_rejects_invalid_json(tmp_path: Path) -> None:
    """Invalid JSON raises a catalog error."""
    path = tmp_path / "manifest.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(CatalogError, match="not valid JSON"):
        TableCatalog.from_manifest(path)


def test_package_columns_match_reference() -> None:
    """The package column data matches the committed reference CSV."""
    with REFERENCE_COLUMNS.open(encoding="utf-8", newline="") as handle:
        import csv

        rows = list(csv.DictReader(handle))
    for table_format in ("tab", "taf"):
        expected = [(row["name"], row["units"]) for row in rows if row["format"] == table_format]
        actual = [(column.name, column.units) for column in load_columns(table_format)]
        assert actual == expected


def test_real_catalog() -> None:
    """A real pair produces a searchable catalog when TIPSY_DATABASE is set."""
    database = os.environ.get("TIPSY_DATABASE")
    if database is None:
        pytest.skip("TIPSY_DATABASE is not set")
    root = Path(database)
    pair = parse_pair(root / "pli0530N00.tab")
    manifest: dict[str, object] = {
        "manifest_version": "1.1.0",
        "generated_at_utc": "2026-11-09T00:00:00Z",
        "extractor": {"name": "fresh-tipsy", "version": "0.1.0", "parser_version": 1},
        "source_install": {"model": "TIPSY", "version": "4.5", "install_env": "TIPSY_INSTALL"},
        "assets": [
            build_tab_manifest_entry(pair.tab, root),
            build_taf_manifest_entry(pair.taf, root),
        ],
    }
    catalog = TableCatalog.from_manifest_data(manifest)
    results = catalog.search(CatalogQuery(species_code="PLI", site_index=20.0, pnc="N"))
    assert len(results) == 2
    assert {entry.format for entry in results} == {"tab", "taf"}
    assert all(entry.stock_height_m == 0.13 for entry in results)

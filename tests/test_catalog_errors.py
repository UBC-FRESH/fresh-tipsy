"""Error-path tests for the table catalog."""

from __future__ import annotations

from copy import deepcopy
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


def _asset(manifest: dict[str, object]) -> dict[str, object]:
    """Return the first asset mapping."""
    assets = manifest["assets"]
    assert isinstance(assets, list)
    asset = assets[0]
    assert isinstance(asset, dict)
    return asset


def test_catalog_rejects_non_object() -> None:
    """A non-object manifest is rejected."""
    with pytest.raises(CatalogError, match="manifest must be an object"):
        TableCatalog.from_manifest_data([])


def test_catalog_rejects_assets_not_list() -> None:
    """A non-list assets field is rejected."""
    manifest = _manifest()
    manifest["assets"] = {}
    with pytest.raises(CatalogError, match="assets must be a list"):
        TableCatalog.from_manifest_data(manifest)


def test_catalog_rejects_asset_not_object() -> None:
    """A non-object asset is rejected."""
    manifest = _manifest()
    manifest["assets"] = [1]
    with pytest.raises(CatalogError, match="must be an object"):
        TableCatalog.from_manifest_data(manifest)


@pytest.mark.parametrize("key", ["source", "table", "metadata", "validation"])
def test_catalog_rejects_missing_blocks(key: str) -> None:
    """Missing required nested blocks are rejected."""
    manifest = _manifest()
    _asset(manifest).pop(key)
    with pytest.raises(CatalogError, match=key):
        TableCatalog.from_manifest_data(manifest)


def test_catalog_rejects_missing_kind() -> None:
    """A missing kind is rejected."""
    manifest = _manifest()
    _asset(manifest).pop("kind")
    with pytest.raises(CatalogError, match="kind"):
        TableCatalog.from_manifest_data(manifest)


def test_catalog_rejects_bad_format() -> None:
    """An unsupported table format is a catalog error."""
    manifest = _manifest()
    table = _asset(manifest)["table"]
    assert isinstance(table, dict)
    table["format"] = "bad"
    with pytest.raises(CatalogError, match="unsupported"):
        TableCatalog.from_manifest_data(manifest)


def test_catalog_rejects_field_count_mismatch() -> None:
    """A field count that disagrees with the column map is rejected."""
    manifest = _manifest()
    table = _asset(manifest)["table"]
    assert isinstance(table, dict)
    table["field_count"] = 23
    with pytest.raises(CatalogError, match="does not match"):
        TableCatalog.from_manifest_data(manifest)


def test_catalog_rejects_inverted_site_range() -> None:
    """An inverted site range is rejected."""
    manifest = _manifest()
    metadata = _asset(manifest)["metadata"]
    assert isinstance(metadata, dict)
    metadata["site_from"] = 20
    metadata["site_to"] = 10
    with pytest.raises(CatalogError, match="inverted"):
        TableCatalog.from_manifest_data(manifest)


def test_catalog_rejects_bad_pnc() -> None:
    """An invalid PNC code is rejected."""
    manifest = _manifest()
    metadata = _asset(manifest)["metadata"]
    assert isinstance(metadata, dict)
    metadata["pnc"] = "X"
    with pytest.raises(CatalogError, match="pnc"):
        TableCatalog.from_manifest_data(manifest)


def test_catalog_rejects_bad_optional_string() -> None:
    """An optional string of the wrong type is rejected."""
    manifest = _manifest()
    table = _asset(manifest)["table"]
    assert isinstance(table, dict)
    table["pair_id"] = 1
    with pytest.raises(CatalogError, match="pair_id"):
        TableCatalog.from_manifest_data(manifest)


def test_catalog_rejects_bad_int() -> None:
    """A non-integer required field is rejected."""
    manifest = _manifest()
    table = _asset(manifest)["table"]
    assert isinstance(table, dict)
    table["data_rows"] = "many"
    with pytest.raises(CatalogError, match="data_rows"):
        TableCatalog.from_manifest_data(manifest)


def test_catalog_rejects_bad_optional_number() -> None:
    """A non-numeric optional field is rejected."""
    manifest = _manifest()
    metadata = _asset(manifest)["metadata"]
    assert isinstance(metadata, dict)
    metadata["stock_height_m"] = "tall"
    with pytest.raises(CatalogError, match="stock_height_m"):
        TableCatalog.from_manifest_data(manifest)


def test_catalog_rejects_bad_string_list() -> None:
    """A non-string list item is rejected."""
    manifest = _manifest()
    table = _asset(manifest)["table"]
    assert isinstance(table, dict)
    table["treatments"] = [1]
    with pytest.raises(CatalogError, match="items must be strings"):
        TableCatalog.from_manifest_data(manifest)


def test_catalog_get_missing() -> None:
    """An unknown asset ID returns None."""
    catalog = TableCatalog.from_manifest_data(_manifest())
    assert catalog.get("missing") is None


def test_catalog_search_without_query() -> None:
    """A missing query returns all entries."""
    catalog = TableCatalog.from_manifest_data(_manifest())
    assert len(catalog.search()) == 2


def test_catalog_filter_misses() -> None:
    """Missed filters return an empty tuple."""
    catalog = TableCatalog.from_manifest_data(_manifest())
    assert catalog.search(CatalogQuery(stock_height_m=9.9)) == ()
    assert catalog.search(CatalogQuery(source_version="9.9")) == ()
    assert catalog.search(CatalogQuery(format="bad")) == ()
    assert catalog.search(CatalogQuery(text="zzz")) == ()


def test_catalog_manifest_missing(tmp_path: Path) -> None:
    """A missing manifest file raises OSError."""
    with pytest.raises(OSError, match="No such file"):
        TableCatalog.from_manifest(tmp_path / "missing.json")


def test_load_columns_unsupported() -> None:
    """An unsupported column-map format raises."""
    with pytest.raises(ValueError, match="unsupported"):
        load_columns("bad")


def test_catalog_deepcopy_isolated() -> None:
    """The helper does not mutate the source manifest."""
    manifest = _manifest()
    copy = deepcopy(manifest)
    TableCatalog.from_manifest_data(copy)
    assert copy == manifest

"""Tests for normalized CSV and Parquet assets."""

from __future__ import annotations

import json
import os
from pathlib import Path

import jsonschema
import pytest

from fresh_tipsy.tables import (
    build_normalized_manifest_entries,
    normalize_table,
    parse_tab_file,
    parse_taf_file,
    verify_round_trip,
    write_normalized_assets,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "data" / "fixtures" / "synthetic"
FIXTURE_TAB = FIXTURES / "syn0010N02.tab"
FIXTURE_TAF = FIXTURES / "syn0010N02.taf"
SCHEMA = ROOT / "notes" / "reference" / "manifest-schema.json"


def test_normalize_tab_preserves_rows() -> None:
    """The compact table normalizes 22 columns and seven rows."""
    normalized = normalize_table(parse_tab_file(FIXTURE_TAB))
    assert normalized.data_rows == 7
    assert len(normalized.columns) == 22
    assert normalized.rows[0].age == 1.0
    assert normalized.rows[0].values[0] == 0.5
    assert len(normalized.rows[0].raw) == 22


def test_normalize_taf_preserves_rows() -> None:
    """The full table normalizes 151 columns and seven rows."""
    normalized = normalize_table(parse_taf_file(FIXTURE_TAF))
    assert normalized.data_rows == 7
    assert len(normalized.columns) == 151
    assert normalized.rows[0].age == 1.0
    assert normalized.rows[0].values[0] == 0.5
    assert len(normalized.rows[0].raw) == 151


def test_normalized_assets_round_trip(tmp_path: Path) -> None:
    """CSV and Parquet round trips match the source rows."""
    normalized = normalize_table(parse_tab_file(FIXTURE_TAB))
    assets = write_normalized_assets(normalized, tmp_path)
    verify_round_trip(normalized, assets)
    assert assets.csv_size_bytes > 0
    assert assets.parquet_size_bytes > 0
    assert len(assets.csv_sha256) == 64
    assert len(assets.parquet_sha256) == 64


def test_normalized_assets_are_deterministic(tmp_path: Path) -> None:
    """The same input produces the same CSV bytes and Parquet values."""
    normalized = normalize_table(parse_tab_file(FIXTURE_TAB))
    first = write_normalized_assets(normalized, tmp_path / "first")
    second = write_normalized_assets(normalized, tmp_path / "second")
    assert first.csv_sha256 == second.csv_sha256
    assert first.parquet_sha256 == second.parquet_sha256


def test_normalized_manifest_entries_validate(tmp_path: Path) -> None:
    """The normalized CSV and Parquet entries validate against the schema."""
    normalized = normalize_table(parse_tab_file(FIXTURE_TAB))
    assets = write_normalized_assets(normalized, tmp_path / "out")
    entries = build_normalized_manifest_entries(normalized, assets, tmp_path / "out", FIXTURES)
    assert len(entries) == 2
    assert {entry["format"] for entry in entries} == {"csv", "parquet"}
    assert all(entry["publication"] == "release_asset" for entry in entries)
    assert all(entry["source_asset_ids"] == ["tipsy45-db-syn0010n02-tab"] for entry in entries)
    manifest: dict[str, object] = {
        "manifest_version": "1.2.0",
        "generated_at_utc": "2026-11-09T00:00:00Z",
        "extractor": {"name": "fresh-tipsy", "version": "0.1.0", "parser_version": 1},
        "source_install": {"model": "TIPSY", "version": "4.5", "install_env": "TIPSY_INSTALL"},
        "assets": entries,
    }
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    jsonschema.validate(manifest, schema)


def test_real_normalized_assets(tmp_path: Path) -> None:
    """A real compact table round-trips when TIPSY_DATABASE is set."""
    database = os.environ.get("TIPSY_DATABASE")
    if database is None:
        pytest.skip("TIPSY_DATABASE is not set")
    root = Path(database)
    normalized = normalize_table(parse_tab_file(root / "pli0530N00.tab"))
    assets = write_normalized_assets(normalized, tmp_path)
    verify_round_trip(normalized, assets)
    assert normalized.data_rows == 276
    assert len(normalized.columns) == 22

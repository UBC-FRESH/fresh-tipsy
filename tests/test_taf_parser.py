"""Tests for the full TIPSY ``.taf`` parser and pair verification."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path

import jsonschema
import pytest

from fresh_tipsy.tables import (
    TAF_COLUMNS_REF,
    TAF_FIELD_COUNT,
    TableFormatError,
    build_taf_manifest_entry,
    parse_pair,
    parse_taf_file,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "data" / "fixtures" / "synthetic"
FIXTURE_TAB = FIXTURES / "syn0010N02.tab"
FIXTURE_TAF = FIXTURES / "syn0010N02.taf"
SCHEMA = ROOT / "notes" / "reference" / "manifest-schema.json"
COLUMN_MAP = ROOT / "notes" / "reference" / "tab-taf-columns.csv"


def test_parse_synthetic_taf() -> None:
    """The synthetic .taf parses into two blocks and a treatment boundary."""
    table = parse_taf_file(FIXTURE_TAF)
    assert table.format == "taf"
    assert table.header.file == "syn0010N02"
    assert table.field_count == TAF_FIELD_COUNT
    assert table.run_count == 2
    assert table.data_rows == 7
    assert table.treatments == ("PCT",)
    assert table.first_age == 1.0
    assert table.last_age == 3.0
    assert len(table.blocks[0].rows[0].fields) == 151
    assert table.blocks[1].boundary_index == 2
    assert table.warnings == ()
    assert table.asset_id == "tipsy45-db-syn0010n02-taf"


def test_parse_pair_verifies_synthetic_tables() -> None:
    """The synthetic .tab and .taf pair verifies cleanly."""
    pair = parse_pair(FIXTURE_TAB)
    assert pair.ok is True
    assert pair.warnings == ()
    assert pair.pair_id == "tipsy45-syn0010n02"
    assert pair.tab.header == pair.taf.header
    assert pair.tab.run_count == pair.taf.run_count
    assert pair.tab.data_rows == pair.taf.data_rows
    assert pair.age_mismatches == ()
    assert pair.age_range_mismatch is False


def test_pair_reports_age_grid_mismatch(tmp_path: Path) -> None:
    """A differing age grid is reported without failing the structural pair."""
    lines = FIXTURE_TAF.read_text(encoding="ascii").splitlines()
    index = next(i for i, line in enumerate(lines) if line.startswith("1\t"))
    fields = lines[index].split("\t")
    fields[0] = "9"
    lines[index] = "\t".join(fields)
    taf_path = tmp_path / "syn0010N02.taf"
    taf_path.write_text("\n".join(lines), encoding="ascii")
    pair = parse_pair(FIXTURE_TAB, taf_path)
    assert pair.ok is True
    assert pair.age_mismatches == (0,)
    assert pair.age_range_mismatch is True


def test_pair_reports_header_mismatch(tmp_path: Path) -> None:
    """A differing .taf header is reported as a pair warning."""
    text = FIXTURE_TAF.read_text(encoding="ascii").replace("File=syn0010N02", "File=other")
    taf_path = tmp_path / "syn0010N02.taf"
    taf_path.write_text(text, encoding="ascii")
    pair = parse_pair(FIXTURE_TAB, taf_path)
    assert pair.ok is False
    assert any("headers differ" in warning for warning in pair.warnings)


def test_taf_field_count_mismatch_raises(tmp_path: Path) -> None:
    """A .taf data row with the wrong field count raises a format error."""
    lines = FIXTURE_TAF.read_text(encoding="ascii").splitlines()
    index = next(i for i, line in enumerate(lines) if line.startswith("1\t"))
    lines[index] = "\t".join(["1"] * 150)
    path = tmp_path / "syn0010N02.taf"
    path.write_text("\n".join(lines), encoding="ascii")
    with pytest.raises(TableFormatError, match="expected 151"):
        parse_taf_file(path)


def test_taf_manifest_entry_validates() -> None:
    """The generated .taf manifest entry validates against the P1.4 schema."""
    table = parse_taf_file(FIXTURE_TAF)
    entry = build_taf_manifest_entry(table, FIXTURES)
    manifest: dict[str, object] = {
        "manifest_version": "1.2.0",
        "generated_at_utc": "2026-11-09T00:00:00Z",
        "extractor": {"name": "fresh-tipsy", "version": "0.1.0", "parser_version": 1},
        "source_install": {"model": "TIPSY", "version": "4.5", "install_env": "TIPSY_INSTALL"},
        "assets": [entry],
    }
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    jsonschema.validate(manifest, schema)
    assert entry["id"] == "tipsy45-db-syn0010n02-taf"
    assert entry["evidence"] == "model_output"
    assert entry["columns_ref"] == TAF_COLUMNS_REF
    assert entry["column_count"] == TAF_FIELD_COUNT
    table_entry = entry["table"]
    assert isinstance(table_entry, dict)
    assert table_entry["data_rows"] == 7


def test_taf_columns_reference_has_151_rows() -> None:
    """The referenced column map has 151 .taf rows."""
    with COLUMN_MAP.open(encoding="utf-8", newline="") as handle:
        rows = [row for row in csv.DictReader(handle) if row["format"] == "taf"]
    assert len(rows) == TAF_FIELD_COUNT


def test_real_taf_pairs() -> None:
    """Every real .tab/.taf pair verifies when TIPSY_DATABASE is configured."""
    database = os.environ.get("TIPSY_DATABASE")
    if database is None:
        pytest.skip("TIPSY_DATABASE is not set")
    paths = sorted(Path(database).glob("*.tab"))
    assert len(paths) == 96
    for path in paths:
        pair = parse_pair(path)
        assert pair.ok is True
        assert pair.tab.field_count == 22
        assert pair.taf.field_count == 151

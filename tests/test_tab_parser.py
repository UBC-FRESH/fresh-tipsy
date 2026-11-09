"""Tests for the compact TIPSY ``.tab`` parser."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path

import jsonschema
import pytest

from fresh_tipsy.tables import (
    TAB_COLUMNS,
    TableFormatError,
    build_tab_manifest_entry,
    parse_filename,
    parse_tab_file,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "data" / "fixtures" / "synthetic" / "syn0010N02.tab"
SCHEMA = ROOT / "notes" / "reference" / "manifest-schema.json"


def test_parse_synthetic_tab() -> None:
    """The synthetic .tab parses into two blocks and a treatment boundary."""
    table = parse_tab_file(FIXTURE)
    assert table.header.file == "syn0010N02"
    assert table.filename.species_code == "SYN"
    assert table.field_count == 22
    assert table.run_count == 2
    assert table.data_rows == 7
    assert table.treatments == ("PCT",)
    assert table.first_age == 1.0
    assert table.last_age == 3.0
    assert len(table.blocks[0].rows[0].fields) == 22
    pct_block = table.blocks[1]
    assert pct_block.marker.pct_density == 500
    assert pct_block.boundary_index == 2
    assert [row.age for row in pct_block.rows] == [1.0, 2.0, 2.0, 3.0]
    assert table.warnings == ()


def test_parse_filename_metadata() -> None:
    """The filename grammar recovers species, site, PNC, PCT, and CT codes."""
    pli = parse_filename("pli0530N00")
    assert (pli.species_code, pli.site_from, pli.site_to) == ("PLI", 5, 30)
    assert (pli.pnc, pli.pct_code, pli.ct_code) == ("N", 0, None)
    ct = parse_filename("fdc1050N0021")
    assert ct.ct_code == 21
    assert ct.site_from == 10
    assert ct.site_to == 50
    spaced = parse_filename("at 1032C04")
    assert (spaced.species_code, spaced.site_from, spaced.site_to) == ("AT", 10, 32)
    assert (spaced.pnc, spaced.pct_code) == ("C", 4)


def test_filename_rejects_invalid_stem() -> None:
    """A non-matching filename raises a format error."""
    with pytest.raises(TableFormatError, match="filename"):
        parse_filename("not-a-table")


def test_header_filename_mismatch_warns(tmp_path: Path) -> None:
    """A header/filename mismatch is recorded as a warning, not a crash."""
    text = FIXTURE.read_text(encoding="ascii")
    changed = text.replace("File=syn0010N02", "File=other")
    path = tmp_path / "syn0010N02.tab"
    path.write_text(changed, encoding="ascii")
    table = parse_tab_file(path)
    assert any("header File" in warning for warning in table.warnings)


def test_wrong_field_count_raises(tmp_path: Path) -> None:
    """A data row with the wrong field count raises a format error."""
    lines = FIXTURE.read_text(encoding="ascii").splitlines()
    index = next(i for i, line in enumerate(lines) if line.startswith("1\t"))
    lines[index] = "\t".join(["1"] * 21)
    path = tmp_path / "syn0010N02.tab"
    path.write_text("\n".join(lines), encoding="ascii")
    with pytest.raises(TableFormatError, match="expected 22"):
        parse_tab_file(path)


def test_manifest_entry_validates() -> None:
    """The generated .tab manifest entry validates against the P1.4 schema."""
    table = parse_tab_file(FIXTURE)
    entry = build_tab_manifest_entry(table, FIXTURE.parent)
    manifest: dict[str, object] = {
        "manifest_version": "1.1.0",
        "generated_at_utc": "2026-11-09T00:00:00Z",
        "extractor": {"name": "fresh-tipsy", "version": "0.1.0", "parser_version": 1},
        "source_install": {"model": "TIPSY", "version": "4.5", "install_env": "TIPSY_INSTALL"},
        "assets": [entry],
    }
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    jsonschema.validate(manifest, schema)
    assert entry["id"] == "tipsy45-db-syn0010n02-tab"
    table_entry = entry["table"]
    assert isinstance(table_entry, dict)
    assert table_entry["data_rows"] == 7
    columns = entry["columns"]
    assert isinstance(columns, list)
    assert len(columns) == 22


def test_tab_columns_match_reference_csv() -> None:
    """The code column map matches the committed reference CSV."""
    path = ROOT / "notes" / "reference" / "tab-taf-columns.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        rows = [row for row in csv.DictReader(handle) if row["format"] == "tab"]
    assert [(row["name"], row["units"]) for row in rows] == [
        (column.name, column.units) for column in TAB_COLUMNS
    ]


def test_real_tab_files() -> None:
    """Every real .tab parses when TIPSY_DATABASE is configured."""
    database = os.environ.get("TIPSY_DATABASE")
    if database is None:
        pytest.skip("TIPSY_DATABASE is not set")
    paths = sorted(Path(database).glob("*.tab"))
    assert len(paths) == 96
    for path in paths:
        table = parse_tab_file(path)
        assert table.field_count == 22
        assert table.warnings == ()

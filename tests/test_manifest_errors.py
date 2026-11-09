"""Error-path tests for manifest entry builders."""

from __future__ import annotations

from pathlib import Path

import pytest

from fresh_tipsy.tables import (
    build_tab_manifest_entry,
    build_table_metadata,
    build_taf_manifest_entry,
    parse_tab_file,
    parse_taf_file,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "data" / "fixtures" / "synthetic"
FIXTURE_TAB = FIXTURES / "syn0010N02.tab"
FIXTURE_TAF = FIXTURES / "syn0010N02.taf"


def _write_tab(tmp_path: Path, name: str = "syn0010N02", header_extra: str = "") -> Path:
    """Write a one-row synthetic .tab file."""
    lines = [
        "[TASS SPECIES]",
        "DatabaseTitle=Synthetic fixture",
        f"File={name}",
        "SpeciesName=Synthetic species",
        "Source=synthetic",
        "Code=SYN",
        "SiteFrom=0",
        "SiteTo=10",
        "TASSsiteIndex=0",
        "TASSsiteSpecies=",
        "PNC=N",
        "PCT=2",
    ]
    if header_extra:
        lines.append(header_extra)
    lines.extend(["", "[RUN,1000,0,0]", "", "\t".join(["1", "1.0", *(["0"] * 20)])])
    path = tmp_path / f"{name}.tab"
    path.write_text("\n".join(lines), encoding="ascii")
    return path


def test_builders_reject_wrong_format() -> None:
    """Each builder rejects the other table format."""
    taf = parse_taf_file(FIXTURE_TAF)
    tab = parse_tab_file(FIXTURE_TAB)
    with pytest.raises(ValueError, match=r"expected a \.tab"):
        build_tab_manifest_entry(taf, FIXTURES)
    with pytest.raises(ValueError, match=r"expected a \.taf"):
        build_taf_manifest_entry(tab, FIXTURES)


def test_builders_reject_path_outside_root(tmp_path: Path) -> None:
    """A source path outside the declared root is rejected."""
    tab = parse_tab_file(FIXTURE_TAB)
    with pytest.raises(ValueError, match="not under source root"):
        build_tab_manifest_entry(tab, tmp_path / "other")


def test_metadata_includes_optional_fields(tmp_path: Path) -> None:
    """Stock and treatment metadata are included when present."""
    path = _write_tab(
        tmp_path,
        name="syn0010N0221",
        header_extra="CT=21\nStockHt=0.13\nStockAge=1.5",
    )
    table = parse_tab_file(path)
    metadata = build_table_metadata(table)
    assert metadata["stock_height_m"] == 0.13
    assert metadata["stock_age_years"] == 1.5
    assert metadata["pct_height_m"] == 2
    assert metadata["ct_height_m"] == 21


def test_manifest_entry_omits_missing_ages(tmp_path: Path) -> None:
    """A table with no numeric age omits the age range."""
    path = _write_tab(tmp_path)
    lines = path.read_text(encoding="ascii").splitlines()
    index = next(i for i, line in enumerate(lines) if line.startswith("1\t"))
    fields = lines[index].split("\t")
    fields[0] = ""
    lines[index] = "\t".join(fields)
    path.write_text("\n".join(lines), encoding="ascii")
    table = parse_tab_file(path)
    entry = build_tab_manifest_entry(table, tmp_path)
    table_entry = entry["table"]
    assert isinstance(table_entry, dict)
    assert "first_age" not in table_entry
    assert "last_age" not in table_entry


def test_manifest_entry_records_warnings(tmp_path: Path) -> None:
    """A header/filename mismatch sets the validation warning status."""
    path = _write_tab(tmp_path)
    lines = path.read_text(encoding="ascii").splitlines()
    lines[2] = "File=other"
    path.write_text("\n".join(lines), encoding="ascii")
    table = parse_tab_file(path)
    entry = build_tab_manifest_entry(table, tmp_path)
    validation = entry["validation"]
    assert isinstance(validation, dict)
    assert validation["status"] == "warn"
    assert validation["warnings"]

"""Error-path and branch tests for the table parsers."""

from __future__ import annotations

from pathlib import Path

import pytest

from fresh_tipsy.tables import (
    TableFormatError,
    parse_filename,
    parse_header,
    parse_pair,
    parse_run_marker,
    parse_tab_file,
)


def _row(age: str = "1", fields: int = 22) -> str:
    """Build a synthetic data row."""
    values = [age, "1.0", *(["0"] * (fields - 2))]
    return "\t".join(values)


def _header(
    *,
    file_name: str = "syn0010N02",
    code: str = "SYN",
    site_from: str = "0",
    site_to: str = "10",
    pnc: str = "N",
    pct: str | None = "2",
    ct: str | None = None,
    extra: str = "",
    rows: list[str] | None = None,
) -> list[str]:
    """Build a synthetic header and run block."""
    lines = [
        "[TASS SPECIES]",
        "DatabaseTitle=Synthetic fixture",
        f"File={file_name}",
        "SpeciesName=Synthetic species",
        "Source=synthetic",
        f"Code={code}",
        f"SiteFrom={site_from}",
        f"SiteTo={site_to}",
        "TASSsiteIndex=0",
        "TASSsiteSpecies=",
        f"PNC={pnc}",
    ]
    if pct is not None:
        lines.append(f"PCT={pct}")
    if ct is not None:
        lines.append(f"CT={ct}")
    if extra:
        lines.append(extra)
    lines.extend(["", "[RUN,1000,0,0]", ""])
    lines.extend(rows if rows is not None else [_row()])
    return lines


def _write_tab(tmp_path: Path, lines: list[str], name: str = "syn0010N02") -> Path:
    """Write a synthetic .tab file."""
    path = tmp_path / f"{name}.tab"
    path.write_text("\n".join(lines), encoding="ascii")
    return path


def _write_taf(tmp_path: Path, lines: list[str], name: str = "syn0010N02") -> Path:
    """Write a synthetic .taf file."""
    path = tmp_path / f"{name}.taf"
    path.write_text("\n".join(lines), encoding="ascii")
    return path


def test_parse_header_errors() -> None:
    """Header failures raise format errors."""
    with pytest.raises(TableFormatError, match="does not start"):
        parse_header([])
    with pytest.raises(TableFormatError, match="does not start"):
        parse_header(["[WRONG]"])
    with pytest.raises(TableFormatError, match="not key=value"):
        parse_header(["[TASS SPECIES]", "oops", "[RUN,1,0,0]"])
    with pytest.raises(TableFormatError, match="no \\[RUN"):
        parse_header(["[TASS SPECIES]", "File=x"])
    with pytest.raises(TableFormatError, match="missing required"):
        parse_header(["[TASS SPECIES]", "[RUN,1,0,0]"])


def test_header_value_errors() -> None:
    """Invalid header values raise format errors."""
    with pytest.raises(TableFormatError, match="PNC"):
        parse_header(_header(pnc="X"))
    with pytest.raises(TableFormatError, match="inverted"):
        parse_header(_header(site_from="10", site_to="5"))
    lines = _header()
    index = lines.index("SiteFrom=0")
    lines[index] = "SiteFrom=oops"
    with pytest.raises(TableFormatError, match="SiteFrom"):
        parse_header(lines)


def test_optional_header_errors() -> None:
    """Invalid optional header values raise format errors."""
    lines = _header(pct=None)
    index = lines.index("[RUN,1000,0,0]")
    lines.insert(index - 1, "PCT=oops")
    with pytest.raises(TableFormatError, match="PCT"):
        parse_header(lines)
    for key in ("StockHt", "StockAge"):
        lines = _header()
        index = lines.index("[RUN,1000,0,0]")
        lines.insert(index - 1, f"{key}=oops")
        with pytest.raises(TableFormatError, match=key):
            parse_header(lines)


def test_header_extra_keys_are_preserved() -> None:
    """Unknown header keys are preserved."""
    header, _ = parse_header(_header(extra="Extra=Value"))
    assert header.extra == (("Extra", "Value"),)


def test_run_marker_errors() -> None:
    """Malformed run markers raise format errors."""
    with pytest.raises(TableFormatError, match="invalid"):
        parse_run_marker("[RUN,1000,0]")


def test_parser_file_errors(tmp_path: Path) -> None:
    """Malformed files raise format errors."""
    with pytest.raises(TableFormatError, match="no \\[RUN"):
        parse_tab_file(_write_tab(tmp_path, ["[TASS SPECIES]", "File=syn0010N02"]))
    path = tmp_path / "syn0010N02.tab"
    path.write_bytes(b"\xff")
    with pytest.raises(TableFormatError, match="not ASCII"):
        parse_tab_file(path)
    with pytest.raises(TableFormatError, match="no data rows"):
        parse_tab_file(_write_tab(tmp_path, _header(rows=[])))
    with pytest.raises(TableFormatError, match="age field"):
        parse_tab_file(_write_tab(tmp_path, _header(rows=[_row(age="abc")])))
    with pytest.raises(TableFormatError, match="expected 22"):
        parse_tab_file(_write_tab(tmp_path, _header(rows=[_row(fields=21)])))
    lines = _header()
    lines[lines.index("[RUN,1000,0,0]")] = "[RUN,1,0]"
    with pytest.raises(TableFormatError, match="invalid"):
        parse_tab_file(_write_tab(tmp_path, lines))


def test_filename_errors() -> None:
    """Invalid and inverted filenames raise format errors."""
    with pytest.raises(TableFormatError, match="filename"):
        parse_filename("bad")
    with pytest.raises(TableFormatError, match="inverted"):
        parse_filename("syn1005N00")


def test_metadata_warnings(tmp_path: Path) -> None:
    """Header/filename mismatches are collected as warnings."""
    lines = _header(code="OTH", site_from="1", site_to="9", pnc="C", pct="4", ct="21")
    table = parse_tab_file(_write_tab(tmp_path, lines))
    assert any("Code" in warning for warning in table.warnings)
    assert any("site range" in warning for warning in table.warnings)
    assert any("PNC" in warning for warning in table.warnings)
    assert any("PCT" in warning for warning in table.warnings)
    assert any("CT" in warning for warning in table.warnings)


def test_pct_ct_treatment_labels(tmp_path: Path) -> None:
    """A marker with both densities gets the combined treatment label."""
    lines = _header()
    lines[lines.index("[RUN,1000,0,0]")] = "[RUN,1000,500,500]"
    table = parse_tab_file(_write_tab(tmp_path, lines))
    assert table.treatments == ("PCT+CT",)


def test_pair_age_grid_warning(tmp_path: Path) -> None:
    """A differing age grid is reported without failing the structural pair."""
    tab = _write_tab(tmp_path, _header())
    taf = _write_taf(tmp_path, _header(rows=[_row(age="9", fields=151)]))
    pair = parse_pair(tab, taf)
    assert pair.ok is True
    assert pair.age_mismatches == (0,)
    assert pair.age_range_mismatch is True


def test_pair_structural_warnings(tmp_path: Path) -> None:
    """Header, run-count, row-count, and pair-ID differences are reported."""
    tab = _write_tab(tmp_path, _header())
    header_mismatch = _write_taf(
        tmp_path,
        _header(file_name="syn0010N03", rows=[_row(fields=151)]),
        "syn0010N03",
    )
    pair = parse_pair(tab, header_mismatch)
    assert any("headers differ" in warning for warning in pair.warnings)
    assert any("pair IDs differ" in warning for warning in pair.warnings)

    run_mismatch = _header(rows=[_row(fields=151)])
    run_mismatch.extend(["", "[RUN,1000,0,0]", "", _row(age="2", fields=151)])
    pair = parse_pair(tab, _write_taf(tmp_path, run_mismatch, "syn0010N02"))
    assert any("run counts differ" in warning for warning in pair.warnings)

    row_mismatch = _header(rows=[_row(fields=151), _row(age="2", fields=151)])
    pair = parse_pair(tab, _write_taf(tmp_path, row_mismatch, "syn0010N02"))
    assert any("data row counts differ" in warning for warning in pair.warnings)
    assert pair.ok is False

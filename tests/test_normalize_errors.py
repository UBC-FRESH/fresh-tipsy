"""Error-path tests for normalized output."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from fresh_tipsy.tables import (
    NormalizationError,
    build_normalized_manifest_entry,
    normalize_table,
    parse_tab_file,
    verify_round_trip,
    write_normalized_assets,
)
from fresh_tipsy.tables.normalize import write_parquet

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "data" / "fixtures" / "synthetic"
FIXTURE_TAB = FIXTURES / "syn0010N02.tab"


def _write_bad_tab(tmp_path: Path) -> Path:
    """Write a one-row .tab with a non-numeric field."""
    text = FIXTURE_TAB.read_text(encoding="ascii")
    lines = text.splitlines()
    index = next(i for i, line in enumerate(lines) if line.startswith("1\t"))
    fields = lines[index].split("\t")
    fields[1] = "abc"
    lines[index] = "\t".join(fields)
    path = tmp_path / "syn0010N02.tab"
    path.write_text("\n".join(lines), encoding="ascii")
    return path


def test_non_numeric_field_raises(tmp_path: Path) -> None:
    """A non-numeric data field is a normalization error."""
    with pytest.raises(NormalizationError, match="not numeric"):
        normalize_table(parse_tab_file(_write_bad_tab(tmp_path)))


def test_column_count_mismatch_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A column-spec count mismatch is a normalization error."""
    monkeypatch.setattr("fresh_tipsy.tables.normalize.load_columns", lambda _: ())
    with pytest.raises(NormalizationError, match="column specifications"):
        normalize_table(parse_tab_file(FIXTURE_TAB))


def test_unsupported_artifact_format(tmp_path: Path) -> None:
    """An unsupported normalized format is rejected."""
    normalized = normalize_table(parse_tab_file(FIXTURE_TAB))
    assets = write_normalized_assets(normalized, tmp_path / "out")
    with pytest.raises(NormalizationError, match="unsupported"):
        build_normalized_manifest_entry(normalized, assets, "json", tmp_path / "out", FIXTURES)


def test_artifact_path_outside_root(tmp_path: Path) -> None:
    """An artifact path outside the output root is rejected."""
    normalized = normalize_table(parse_tab_file(FIXTURE_TAB))
    assets = write_normalized_assets(normalized, tmp_path / "out")
    with pytest.raises(NormalizationError, match="outside"):
        build_normalized_manifest_entry(normalized, assets, "csv", tmp_path / "other", FIXTURES)


def test_source_path_outside_root(tmp_path: Path) -> None:
    """A source path outside the source root is rejected."""
    normalized = normalize_table(parse_tab_file(FIXTURE_TAB))
    assets = write_normalized_assets(normalized, tmp_path / "out")
    with pytest.raises(NormalizationError, match="outside"):
        build_normalized_manifest_entry(
            normalized, assets, "csv", tmp_path / "out", tmp_path / "other"
        )


def test_csv_header_mismatch(tmp_path: Path) -> None:
    """A modified CSV header fails the round trip."""
    normalized = normalize_table(parse_tab_file(FIXTURE_TAB))
    assets = write_normalized_assets(normalized, tmp_path)
    rows = list(csv.reader(assets.csv_path.open(encoding="ascii", newline="")))
    rows[0][0] = "wrong"
    with assets.csv_path.open("w", encoding="ascii", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerows(rows)
    with pytest.raises(NormalizationError, match="header"):
        verify_round_trip(normalized, assets)


def test_csv_row_mismatch(tmp_path: Path) -> None:
    """A modified CSV row fails the round trip."""
    normalized = normalize_table(parse_tab_file(FIXTURE_TAB))
    assets = write_normalized_assets(normalized, tmp_path)
    rows = list(csv.reader(assets.csv_path.open(encoding="ascii", newline="")))
    rows[1][1] = "999"
    with assets.csv_path.open("w", encoding="ascii", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerows(rows)
    with pytest.raises(NormalizationError, match="rows"):
        verify_round_trip(normalized, assets)


def test_parquet_row_count_mismatch(tmp_path: Path) -> None:
    """A modified Parquet row count fails the round trip."""
    normalized = normalize_table(parse_tab_file(FIXTURE_TAB))
    assets = write_normalized_assets(normalized, tmp_path)
    pq.write_table(pa.table({"only": [1.0]}), assets.parquet_path)
    with pytest.raises(NormalizationError, match="row count"):
        verify_round_trip(normalized, assets)


def test_parquet_column_mismatch(tmp_path: Path) -> None:
    """Modified Parquet columns fail the round trip."""
    normalized = normalize_table(parse_tab_file(FIXTURE_TAB))
    assets = write_normalized_assets(normalized, tmp_path)
    pq.write_table(pa.table({"only": [1.0] * 7}), assets.parquet_path)
    with pytest.raises(NormalizationError, match="columns"):
        verify_round_trip(normalized, assets)


def test_write_parquet_without_pyarrow(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A missing pyarrow install produces a normalization error."""
    monkeypatch.setitem(sys.modules, "pyarrow", None)
    monkeypatch.setitem(sys.modules, "pyarrow.parquet", None)
    normalized = normalize_table(parse_tab_file(FIXTURE_TAB))
    with pytest.raises(NormalizationError, match="pyarrow"):
        write_parquet(normalized, tmp_path / "data.parquet")

"""Integration tests for the fresh-tipsy database CLI."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from fresh_tipsy.cli import app, main

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "data" / "fixtures" / "synthetic"


def _extract(tmp_path: Path) -> Path:
    """Run the extract command and return the manifest path."""
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["db", "extract", "--source", str(FIXTURES), "--out", str(tmp_path / "out")],
    )
    assert result.exit_code == 0, result.output
    return tmp_path / "out" / "manifest.json"


def test_extract_writes_manifest(tmp_path: Path) -> None:
    """Extract writes source and normalized entries."""
    manifest_path = _extract(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assets = manifest["assets"]
    assert isinstance(assets, list)
    assert len(assets) == 6
    kinds = [asset["kind"] for asset in assets]
    assert kinds.count("tipsy_table") == 2
    assert kinds.count("normalized_table") == 4


def test_extract_json_summary(tmp_path: Path) -> None:
    """Extract --json reports table and asset counts."""
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "db",
            "extract",
            "--source",
            str(FIXTURES),
            "--out",
            str(tmp_path / "out"),
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    summary = json.loads(result.stdout)
    assert summary["status"] == "ok"
    assert summary["tables"] == 1
    assert summary["assets"] == 6
    assert summary["normalized_assets"] == 4
    assert summary["age_mismatch_pairs"] == 0


def test_validate_manifest(tmp_path: Path) -> None:
    """Validate accepts the extracted manifest and source files."""
    manifest_path = _extract(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "db",
            "validate",
            "--catalog",
            str(manifest_path),
            "--source",
            str(FIXTURES),
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    summary = json.loads(result.stdout)
    assert summary["status"] == "ok"
    assert summary["errors"] == []
    assert summary["tables"] == 2


def test_validate_without_source_warns(tmp_path: Path) -> None:
    """Validate without a source root skips raw checks with a warning."""
    manifest_path = _extract(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["db", "validate", "--catalog", str(manifest_path), "--json"],
    )
    assert result.exit_code == 0, result.output
    summary = json.loads(result.stdout)
    assert summary["status"] == "ok"
    assert any("source checks skipped" in warning for warning in summary["warnings"])


def test_validate_corrupt_manifest(tmp_path: Path) -> None:
    """A malformed manifest fails validation."""
    path = tmp_path / "manifest.json"
    path.write_text('{"assets": []}', encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["db", "validate", "--catalog", str(path), "--json"],
    )
    assert result.exit_code == 1
    summary = json.loads(result.stdout)
    assert summary["status"] == "error"
    assert summary["errors"]


def test_catalog_filters_and_json(tmp_path: Path) -> None:
    """Catalog filters return both formats for the synthetic pair."""
    manifest_path = _extract(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "db",
            "catalog",
            "--catalog",
            str(manifest_path),
            "--species",
            "SYN",
            "--site-index",
            "5",
            "--pnc",
            "N",
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    summary = json.loads(result.stdout)
    assert summary["count"] == 2
    assert {table["format"] for table in summary["tables"]} == {"tab", "taf"}


def test_catalog_empty_result(tmp_path: Path) -> None:
    """An unsupported filter returns an explicit empty result."""
    manifest_path = _extract(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "db",
            "catalog",
            "--catalog",
            str(manifest_path),
            "--species",
            "PLI",
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    summary = json.loads(result.stdout)
    assert summary["count"] == 0
    assert summary["tables"] == []


def test_extract_missing_source(tmp_path: Path) -> None:
    """A missing source directory fails with a clear error."""
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "db",
            "extract",
            "--source",
            str(tmp_path / "missing"),
            "--out",
            str(tmp_path / "out"),
        ],
    )
    assert result.exit_code == 1
    assert "does not exist" in result.output


def test_db_help() -> None:
    """The db command group has help."""
    runner = CliRunner()
    result = runner.invoke(app, ["db", "--help"])
    assert result.exit_code == 0
    assert "extract" in result.stdout
    assert "validate" in result.stdout
    assert "catalog" in result.stdout


def test_real_cli_extract(tmp_path: Path) -> None:
    """A real pair extracts, validates, and catalogs when TIPSY_DATABASE is set."""
    database = os.environ.get("TIPSY_DATABASE")
    if database is None:
        pytest.skip("TIPSY_DATABASE is not set")
    root = Path(database)
    source = tmp_path / "source"
    source.mkdir()
    for suffix in ("tab", "taf"):
        shutil.copyfile(root / f"pli0530N00.{suffix}", source / f"pli0530N00.{suffix}")
    runner = CliRunner()
    extract_result = runner.invoke(
        app,
        [
            "db",
            "extract",
            "--source",
            str(source),
            "--out",
            str(tmp_path / "out"),
            "--json",
        ],
    )
    assert extract_result.exit_code == 0, extract_result.output
    summary = json.loads(extract_result.stdout)
    assert summary["tables"] == 1
    assert summary["assets"] == 6
    manifest = Path(summary["manifest"])
    validate_result = runner.invoke(
        app,
        [
            "db",
            "validate",
            "--catalog",
            str(manifest),
            "--source",
            str(source),
            "--json",
        ],
    )
    assert validate_result.exit_code == 0, validate_result.output
    catalog_result = runner.invoke(
        app,
        [
            "db",
            "catalog",
            "--catalog",
            str(manifest),
            "--species",
            "PLI",
            "--site-index",
            "20",
            "--pnc",
            "N",
            "--json",
        ],
    )
    assert catalog_result.exit_code == 0, catalog_result.output
    catalog_summary = json.loads(catalog_result.stdout)
    assert catalog_summary["count"] == 2
    assert {table["format"] for table in catalog_summary["tables"]} == {"tab", "taf"}


def test_extract_non_json(tmp_path: Path) -> None:
    """Extract prints a human-readable summary."""
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["db", "extract", "--source", str(FIXTURES), "--out", str(tmp_path / "out")],
    )
    assert result.exit_code == 0, result.output
    assert "Extracted 1 table pairs" in result.stdout


def test_extract_no_tab_files(tmp_path: Path) -> None:
    """An empty source directory fails."""
    source = tmp_path / "empty"
    source.mkdir()
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["db", "extract", "--source", str(source), "--out", str(tmp_path / "out")],
    )
    assert result.exit_code == 1
    assert "no .tab files" in result.output


def test_extract_pair_warning_fails(tmp_path: Path) -> None:
    """A structurally broken pair fails extraction."""
    source = tmp_path / "source"
    source.mkdir()
    for suffix in ("tab", "taf"):
        shutil.copyfile(FIXTURES / f"syn0010N02.{suffix}", source / f"syn0010N02.{suffix}")
    tab = source / "syn0010N02.tab"
    tab.write_text(
        tab.read_text(encoding="ascii").replace("File=syn0010N02", "File=other"),
        encoding="ascii",
    )
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["db", "extract", "--source", str(source), "--out", str(tmp_path / "out")],
    )
    assert result.exit_code == 1
    assert "headers differ" in result.output


def test_extract_records_age_grid_gap(tmp_path: Path) -> None:
    """A pair with different age grids is extracted with a gap record."""
    source = tmp_path / "source"
    source.mkdir()
    for suffix in ("tab", "taf"):
        shutil.copyfile(FIXTURES / f"syn0010N02.{suffix}", source / f"syn0010N02.{suffix}")
    taf = source / "syn0010N02.taf"
    lines = taf.read_text(encoding="ascii").splitlines()
    index = next(i for i, line in enumerate(lines) if line.startswith("1\t"))
    fields = lines[index].split("\t")
    fields[0] = "9"
    lines[index] = "\t".join(fields)
    taf.write_text("\n".join(lines), encoding="ascii")
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "db",
            "extract",
            "--source",
            str(source),
            "--out",
            str(tmp_path / "out"),
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    summary = json.loads(result.stdout)
    assert summary["age_mismatch_pairs"] == 1
    assert summary["gaps"][0]["id"] == "taf-tab-age-grid-mismatch"


def test_validate_non_json(tmp_path: Path) -> None:
    """Validate prints a human-readable success summary."""
    manifest_path = _extract(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["db", "validate", "--catalog", str(manifest_path)],
    )
    assert result.exit_code == 0, result.output
    assert "Manifest valid." in result.stdout


def test_validate_missing_manifest(tmp_path: Path) -> None:
    """A missing manifest fails validation."""
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["db", "validate", "--catalog", str(tmp_path / "missing.json")],
    )
    assert result.exit_code == 1
    assert "does not exist" in result.output


def test_catalog_non_json(tmp_path: Path) -> None:
    """Catalog prints matching rows and an explicit empty result."""
    manifest_path = _extract(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["db", "catalog", "--catalog", str(manifest_path), "--species", "SYN"],
    )
    assert result.exit_code == 0, result.output
    assert "syn0010n02" in result.stdout
    empty = runner.invoke(
        app,
        ["db", "catalog", "--catalog", str(manifest_path), "--species", "PLI"],
    )
    assert empty.exit_code == 0
    assert "No tables matched." in empty.stdout


def test_catalog_missing_manifest(tmp_path: Path) -> None:
    """A missing manifest fails catalog loading."""
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["db", "catalog", "--catalog", str(tmp_path / "missing.json")],
    )
    assert result.exit_code == 1
    assert "does not exist" in result.output


def test_manifest_validation_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A manifest validation error fails extraction."""
    monkeypatch.setattr("fresh_tipsy.cli.validate_manifest_data", lambda _: ["boom"])
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["db", "extract", "--source", str(FIXTURES), "--out", str(tmp_path / "out")],
    )
    assert result.exit_code == 1
    assert "manifest validation failed" in result.output


def test_main_help(monkeypatch: pytest.MonkeyPatch) -> None:
    """The module entry point runs the Typer app."""
    monkeypatch.setattr("sys.argv", ["fresh-tipsy", "--help"])
    with pytest.raises(SystemExit):
        main()

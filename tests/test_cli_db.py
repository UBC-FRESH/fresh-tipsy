"""Integration tests for the fresh-tipsy database CLI."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from fresh_tipsy.cli import app

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

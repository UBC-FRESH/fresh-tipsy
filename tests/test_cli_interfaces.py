"""Integration tests for curve, product, and economics CLI commands."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from fresh_tipsy.cli import app

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "data" / "fixtures" / "synthetic"


def _header() -> list[str]:
    """Build a synthetic header for the CLI product pair."""
    return [
        "[TASS SPECIES]",
        "DatabaseTitle=Synthetic CLI fixture",
        "File=syn0010N00",
        "SpeciesName=Synthetic species",
        "Source=synthetic",
        "Code=SYN",
        "SiteFrom=0",
        "SiteTo=10",
        "TASSsiteIndex=0",
        "TASSsiteSpecies=",
        "PNC=N",
        "",
        "[RUN,1000,0,0]",
        "",
    ]


def _tab_row() -> list[str]:
    """Build a compact row for the CLI product pair."""
    fields = ["0"] * 22
    fields[0] = "5"
    fields[1] = "10"
    fields[2] = "100"
    return fields


def _taf_row() -> list[str]:
    """Build a product row with known values."""
    fields = ["0"] * 151
    fields[0] = "5"
    fields[1] = "10"
    for offset, value in enumerate(("10", "20", "30", "40"), start=2):
        fields[offset] = value
    for offset, value in enumerate(("1", "2", "3", "4", "5"), start=6):
        fields[offset] = value
    for offset, value in enumerate(("1", "2", "3", "4", "5", "6", "7", "8"), start=68):
        fields[offset] = value
    fields[91] = "10"
    fields[92] = "20"
    fields[93] = "30"
    fields[94] = "40"
    return fields


def _extract_product_pair(tmp_path: Path) -> tuple[Path, Path]:
    """Write a synthetic product pair and extract a manifest."""
    source = tmp_path / "source"
    source.mkdir()
    (source / "syn0010N00.tab").write_text(
        "\n".join([*_header(), "\t".join(_tab_row())]), encoding="ascii"
    )
    (source / "syn0010N00.taf").write_text(
        "\n".join([*_header(), "\t".join(_taf_row())]), encoding="ascii"
    )
    out = tmp_path / "out"
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["db", "extract", "--source", str(source), "--out", str(out), "--json"],
    )
    assert result.exit_code == 0, result.output
    return source, Path(json.loads(result.stdout)["manifest"])


def _curve_manifest(tmp_path: Path) -> tuple[Path, Path]:
    """Extract the committed synthetic curve fixture."""
    out = tmp_path / "curve-out"
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["db", "extract", "--source", str(FIXTURES), "--out", str(out), "--json"],
    )
    assert result.exit_code == 0, result.output
    return FIXTURES, Path(json.loads(result.stdout)["manifest"])


def test_curve_query_json(tmp_path: Path) -> None:
    """Curve query returns metrics, provenance, and the query."""
    source, manifest = _curve_manifest(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "curve",
            "query",
            "--catalog",
            str(manifest),
            "--source",
            str(source),
            "--species",
            "SYN",
            "--site-index",
            "5",
            "--age",
            "2",
            "--format",
            "tab",
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    summary = json.loads(result.stdout)
    assert summary["status"] == "ok"
    assert summary["request"]["query"]["species_code"] == "SYN"
    assert summary["result"]["height_site_m"] == 1.0
    assert summary["result"]["provenance"]["sha256"]
    assert summary["evidence"] == "source_table"


def test_product_recover_json(tmp_path: Path) -> None:
    """Product recovery returns totals and mass-balance checks."""
    source, manifest = _extract_product_pair(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "product",
            "recover",
            "--catalog",
            str(manifest),
            "--source",
            str(source),
            "--species",
            "SYN",
            "--site-index",
            "5",
            "--age",
            "5",
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    summary = json.loads(result.stdout)
    assert summary["status"] == "ok"
    assert summary["result"]["totals"]["lumber_2_or_better_bf_ha"] == 100.0
    assert summary["result"]["species_code"] == "SYN"
    checks = {check["name"]: check for check in summary["result"]["checks"]}
    assert checks["lumber_2_or_better_vs_graded"]["status"] == "pass"


def test_econ_run_json(tmp_path: Path) -> None:
    """Economics runs an explicit scenario and reports provenance."""
    source, manifest = _extract_product_pair(tmp_path)
    scenario = {
        "query": {
            "species_code": "SYN",
            "site_index": 5,
            "age": 5,
            "pnc": "N",
            "format": "taf",
        },
        "period": "test",
        "revenue_groups": ["lumber_2_or_better"],
        "prices": [
            {
                "species_code": "SYN",
                "group": "lumber_2_or_better",
                "period": "test",
                "price_per_unit": 1000.0,
                "unit": "CAD/mbf",
                "source": "test price",
                "citation": "Synthetic test input.",
            }
        ],
        "costs": [
            {
                "category": "regeneration",
                "age": 0,
                "amount_per_ha": 50.0,
                "label": "test cost",
                "source": "test cost",
                "citation": "Synthetic test input.",
            }
        ],
        "assumptions": {"discount_rate": 0.10},
    }
    scenario_path = tmp_path / "scenario.json"
    scenario_path.write_text(json.dumps(scenario), encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "econ",
            "run",
            "--catalog",
            str(manifest),
            "--source",
            str(source),
            "--scenario",
            str(scenario_path),
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    summary = json.loads(result.stdout)
    assert summary["status"] == "ok"
    assert summary["result"]["revenue_per_ha"] == 100.0
    assert summary["result"]["npv_per_ha"] == pytest.approx(12.092, abs=1e-3)
    assert summary["result"]["provenance"]["source_model"] == "TIPSY"
    assert summary["request"]["scenario"]["query"]["format"] == "taf"


def test_cli_errors_are_nonzero(tmp_path: Path) -> None:
    """Missing manifests and malformed scenarios fail explicitly."""
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "curve",
            "query",
            "--catalog",
            str(tmp_path / "missing.json"),
            "--source",
            str(tmp_path),
            "--species",
            "SYN",
            "--site-index",
            "5",
            "--age",
            "2",
        ],
    )
    assert result.exit_code == 1
    assert "manifest does not exist" in result.output
    scenario = tmp_path / "bad.json"
    scenario.write_text("[]", encoding="utf-8")
    result = runner.invoke(
        app,
        [
            "econ",
            "run",
            "--catalog",
            str(tmp_path / "missing.json"),
            "--scenario",
            str(scenario),
        ],
    )
    assert result.exit_code == 1
    assert "JSON object" in result.output


def test_new_command_help() -> None:
    """The new command groups are discoverable."""
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "curve" in result.stdout
    assert "product" in result.stdout
    assert "econ" in result.stdout

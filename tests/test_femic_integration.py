"""Tests for the optional FEMIC adapter."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from fresh_tipsy.api.service import browse_catalog
from fresh_tipsy.cli import app
from fresh_tipsy.integrations import (
    asset_provenance,
    query_growth,
    recover_products,
    run_economics,
)
from fresh_tipsy.tables import CatalogQuery

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "data" / "fixtures" / "synthetic"


def _manifest(tmp_path: Path) -> Path:
    """Extract the synthetic fixture and return its manifest."""
    out = tmp_path / "out"
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["db", "extract", "--source", str(FIXTURES), "--out", str(out), "--json"],
    )
    assert result.exit_code == 0, result.output
    return Path(json.loads(result.stdout)["manifest"])


def _query(*, table_format: str = "tab") -> dict[str, object]:
    """Return a synthetic growth query mapping."""
    return {
        "species_code": "SYN",
        "site_index": 5,
        "age": 2,
        "pnc": "N",
        "format": table_format,
    }


def test_femic_query_passes_provenance(tmp_path: Path) -> None:
    """The adapter passes package version, manifest hash, and provenance."""
    manifest = _manifest(tmp_path)
    result = query_growth(manifest, FIXTURES, _query())
    assert result.status == "ok"
    assert result.result is not None
    assert result.result["height_site_m"] == 1.0
    assert result.provenance is not None
    assert result.provenance["sha256"]
    assert result.package_version == "0.1.0"
    assert result.manifest_sha256 is not None
    assert result.as_dict()["fresh_tipsy_version"] == "0.1.0"


def test_femic_product_and_economics(tmp_path: Path) -> None:
    """The adapter wraps product and economics calls."""
    manifest = _manifest(tmp_path)
    product = recover_products(manifest, FIXTURES, _query(table_format="tab"))
    assert product.status == "ok"
    assert product.evidence == "model_output"
    scenario: dict[str, object] = {
        "query": _query(table_format="taf"),
        "revenue_groups": ["lumber_2_or_better"],
        "prices": [],
        "costs": [],
        "assumptions": {"discount_rate": 0.10},
    }
    economics = run_economics(manifest, FIXTURES, scenario)
    assert economics.status == "ok"
    assert economics.result is not None
    assert economics.result["cost_per_ha"] == 0.0


def test_femic_asset_provenance(tmp_path: Path) -> None:
    """Asset provenance is available through the adapter."""
    manifest = _manifest(tmp_path)
    entries = browse_catalog(manifest, CatalogQuery(species_code="SYN")).result
    assert entries is not None
    tables = entries["tables"]
    assert isinstance(tables, list)
    first = tables[0]
    assert isinstance(first, dict)
    result = asset_provenance(manifest, str(first["id"]))
    assert result.status == "ok"
    assert result.provenance is not None
    assert result.manifest_sha256


def test_femic_errors_are_structured(tmp_path: Path) -> None:
    """Adapter failures carry a code and do not fabricate a result."""
    manifest = _manifest(tmp_path)
    bad = query_growth(manifest, FIXTURES, {"species_code": "SYN"})
    assert bad.status == "error"
    assert bad.error is not None
    assert bad.error["code"] == "invalid_request"
    missing = asset_provenance(manifest, "not-a-table")
    assert missing.status == "error"
    assert missing.error is not None
    assert missing.error["code"] == "not_found"

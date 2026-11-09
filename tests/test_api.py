"""Tests for the shared service layer and FastAPI endpoints."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from fresh_tipsy.api.app import create_app
from fresh_tipsy.api.service import (
    ServiceError,
    asset_provenance,
    browse_catalog,
    health,
    parse_scenario,
    query_curve,
    recover_products,
    run_economics,
)
from fresh_tipsy.cli import app
from fresh_tipsy.curves import CurveQuery
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


def _client(tmp_path: Path) -> TestClient:
    """Build an API client for the synthetic fixture."""
    return TestClient(create_app(_manifest(tmp_path), FIXTURES))


def _query(*, age: float = 2.0, table_format: str = "tab") -> CurveQuery:
    """Return a synthetic growth query."""
    return CurveQuery("SYN", 5.0, age=age, pnc="N", format=table_format)


def _scenario_data() -> dict[str, object]:
    """Return a valid economics scenario mapping."""
    return {
        "query": {
            "species_code": "SYN",
            "site_index": 5,
            "age": 2,
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


def test_health_and_not_configured() -> None:
    """Health works without a catalog; data endpoints fail explicitly."""
    client = TestClient(create_app())
    health_response = client.get("/health")
    assert health_response.status_code == 200
    assert health_response.json()["status"] == "ok"
    missing = client.get("/catalog")
    assert missing.status_code == 503
    assert missing.json()["error"]["code"] == "not_configured"


def test_service_health_and_catalog(tmp_path: Path) -> None:
    """Service functions are callable without HTTP."""
    manifest = _manifest(tmp_path)
    assert health().as_dict()["status"] == "ok"
    response = browse_catalog(manifest, CatalogQuery(species_code="SYN"))
    assert response.status == "ok"
    assert response.result is not None
    assert response.result["count"] == 2
    tables = response.result["tables"]
    assert isinstance(tables, list)
    asset_id = tables[0]["id"]
    provenance = asset_provenance(manifest, str(asset_id))
    assert provenance.status == "ok"
    assert provenance.provenance is not None
    assert provenance.provenance["sha256"]


def test_curve_service_and_api(tmp_path: Path) -> None:
    """Curve service and API return the same typed envelope."""
    manifest = _manifest(tmp_path)
    service_response = query_curve(manifest, FIXTURES, _query())
    assert service_response.status == "ok"
    assert service_response.provenance is not None
    assert service_response.provenance["sha256"]
    client = TestClient(create_app(manifest, FIXTURES))
    response = client.post(
        "/curves/query",
        json={
            "species_code": "SYN",
            "site_index": 5,
            "age": 2,
            "pnc": "N",
            "format": "tab",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["request"]["query"]["species_code"] == "SYN"
    assert payload["result"]["height_site_m"] == 1.0
    assert payload["provenance"]["evidence"] == "source_table"


def test_product_service_and_api(tmp_path: Path) -> None:
    """Product recovery works through service and API."""
    manifest = _manifest(tmp_path)
    service_response = recover_products(manifest, FIXTURES, _query(table_format="taf"))
    assert service_response.status == "ok"
    assert service_response.evidence == "model_output"
    client = TestClient(create_app(manifest, FIXTURES))
    response = client.post(
        "/products/recover",
        json={
            "species_code": "SYN",
            "site_index": 5,
            "age": 2,
            "pnc": "N",
            "format": "taf",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["result"]["species_code"] == "SYN"


def test_economics_service_and_api(tmp_path: Path) -> None:
    """Economics service and API share the scenario parser and result."""
    manifest = _manifest(tmp_path)
    scenario = parse_scenario(_scenario_data())
    service_response = run_economics(manifest, FIXTURES, scenario)
    assert service_response.status == "ok"
    assert service_response.result is not None
    assert service_response.result["cost_per_ha"] == 50.0
    client = TestClient(create_app(manifest, FIXTURES))
    response = client.post("/economics/run", json=_scenario_data())
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["result"]["npv_per_ha"] == pytest.approx(-50.0)
    assert payload["request"]["scenario"]["period"] == "test"


def test_catalog_and_provenance_endpoints(tmp_path: Path) -> None:
    """Catalog, table, and provenance endpoints expose source metadata."""
    client = _client(tmp_path)
    catalog = client.get("/catalog", params={"species": "SYN", "site_index": 5})
    assert catalog.status_code == 200
    payload = catalog.json()
    assert payload["status"] == "ok"
    assert payload["result"]["count"] == 2
    asset_id = payload["result"]["tables"][0]["id"]
    table = client.get(f"/catalog/{asset_id}")
    assert table.status_code == 200
    assert table.json()["result"]["id"] == asset_id
    provenance = client.get(f"/provenance/{asset_id}")
    assert provenance.status_code == 200
    assert provenance.json()["provenance"]["sha256"]


def test_api_errors_are_structured(tmp_path: Path) -> None:
    """Unsupported, missing, and invalid requests return structured errors."""
    client = _client(tmp_path)
    unsupported = client.post(
        "/curves/query",
        json={"species_code": "NOPE", "site_index": 5, "age": 2},
    )
    assert unsupported.status_code == 422
    assert unsupported.json()["error"]["code"] == "query_failed"
    wrong_format = client.post(
        "/products/recover",
        json={"species_code": "SYN", "site_index": 5, "age": 2, "format": "tab"},
    )
    assert wrong_format.status_code == 422
    assert wrong_format.json()["error"]["code"] == "product_failed"
    missing_asset = client.get("/provenance/missing")
    assert missing_asset.status_code == 404
    assert missing_asset.json()["error"]["code"] == "not_found"
    validation = client.post("/economics/run", json={"query": {}})
    assert validation.status_code == 422
    assert validation.json()["error"]["code"] == "invalid_request"


def test_parse_scenario_rejects_bad_inputs() -> None:
    """Scenario parser errors are structured and specific."""
    with pytest.raises(ServiceError, match="revenue_groups"):
        parse_scenario({"query": _scenario_data()["query"]})
    bad_price = _scenario_data()
    bad_price["prices"] = [{"group": "lumber_2_or_better"}]
    with pytest.raises(ServiceError, match="prices"):
        parse_scenario(bad_price)
    bad_cost = _scenario_data()
    bad_cost["costs"] = [{"category": "regeneration"}]
    with pytest.raises(ServiceError, match="costs"):
        parse_scenario(bad_cost)
    bad_assumptions = _scenario_data()
    bad_assumptions["assumptions"] = {}
    with pytest.raises(ServiceError, match="assumptions"):
        parse_scenario(bad_assumptions)
    bad_groups = _scenario_data()
    bad_groups["revenue_groups"] = ["not_a_group"]
    with pytest.raises(ServiceError, match="revenue_groups"):
        parse_scenario(bad_groups)

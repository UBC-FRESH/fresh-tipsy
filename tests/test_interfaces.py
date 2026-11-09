"""Cross-interface parity and contract tests."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import cast

import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from fresh_tipsy.agent import ToolBox
from fresh_tipsy.api.app import create_app
from fresh_tipsy.api.service import (
    parse_scenario,
    query_curve,
    recover_products,
    run_economics,
)
from fresh_tipsy.cli import app
from fresh_tipsy.curves import CurveQuery
from fresh_tipsy.web.app import create_web_app

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "data" / "fixtures" / "synthetic"
ENVELOPE_KEYS = {
    "status",
    "request",
    "result",
    "provenance",
    "evidence",
    "warnings",
    "error",
}


def _product_source(tmp_path: Path) -> tuple[Path, Path]:
    """Build a synthetic pair with product values and a manifest."""
    source = tmp_path / "source"
    source.mkdir()
    for suffix in ("tab", "taf"):
        shutil.copyfile(FIXTURES / f"syn0010N02.{suffix}", source / f"syn0010N02.{suffix}")
    taf = source / "syn0010N02.taf"
    lines = taf.read_text(encoding="ascii").splitlines()
    for index, line in enumerate(lines):
        if line and line[0].isdigit():
            fields = line.split("\t")
            for offset, value in enumerate(("10", "20", "30", "40"), start=2):
                fields[offset] = value
            for offset, value in enumerate(("10", "20", "30", "40"), start=91):
                fields[offset] = value
            lines[index] = "\t".join(fields)
    taf.write_text("\n".join(lines), encoding="ascii")
    out = tmp_path / "out"
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["db", "extract", "--source", str(source), "--out", str(out), "--json"],
    )
    assert result.exit_code == 0, result.output
    return source, Path(json.loads(result.stdout)["manifest"])


def _query(*, table_format: str = "tab") -> CurveQuery:
    """Return the synthetic parity query."""
    return CurveQuery("SYN", 5.0, age=2.0, pnc="N", format=table_format)


def _scenario(*, with_price: bool = True) -> dict[str, object]:
    """Return a parity economics scenario."""
    prices = (
        [
            {
                "species_code": "SYN",
                "group": "lumber_2_or_better",
                "period": "test",
                "price_per_unit": 1000.0,
                "unit": "CAD/mbf",
                "source": "test price",
                "citation": "Synthetic test input.",
            }
        ]
        if with_price
        else []
    )
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
        "prices": prices,
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


def _dict(value: object) -> dict[str, object]:
    """Narrow an object to a dictionary."""
    assert isinstance(value, dict)
    return cast(dict[str, object], value)


def _list(value: object) -> list[object]:
    """Narrow an object to a list."""
    assert isinstance(value, list)
    return list(value)


def _cli_json(tmp_path: Path, args: list[str]) -> dict[str, object]:
    """Run a CLI command and parse its JSON output."""
    runner = CliRunner()
    result = runner.invoke(app, [*args, "--json"])
    assert result.exit_code == 0, result.output
    return _dict(json.loads(result.stdout))


def test_curve_parity_and_envelope(tmp_path: Path) -> None:
    """CLI, API, and assistant return the same curve values and provenance."""
    source, manifest = _product_source(tmp_path)
    service = query_curve(manifest, source, _query())
    cli = _cli_json(
        tmp_path,
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
            "--pnc",
            "N",
        ],
    )
    api = (
        TestClient(create_app(manifest, source))
        .post(
            "/curves/query",
            json={
                "species_code": "SYN",
                "site_index": 5,
                "age": 2,
                "pnc": "N",
                "format": "tab",
            },
        )
        .json()
    )
    agent = (
        ToolBox(manifest, source)
        .query_curve(
            {"species_code": "SYN", "site_index": 5, "age": 2, "pnc": "N", "format": "tab"}
        )
        .as_dict()
    )
    web = TestClient(create_web_app(manifest, source)).get(
        "/ui/curve",
        params={"species": "SYN", "site_index": 5, "age": 2, "format": "tab"},
    )
    assert web.status_code == 200
    assert "Site height" in web.text
    for payload in (service.as_dict(), cli, api, agent):
        assert set(payload) >= ENVELOPE_KEYS
        result = _dict(payload["result"])
        provenance = _dict(payload["provenance"])
        assert result["height_site_m"] == 1.0
        assert str(provenance["relative_path"]).endswith("syn0010N02.tab")
    assert "syn0010N02.tab" in web.text


def test_product_parity(tmp_path: Path) -> None:
    """Product totals and checks agree across interfaces."""
    source, manifest = _product_source(tmp_path)
    service = recover_products(manifest, source, _query(table_format="taf"))
    cli = _cli_json(
        tmp_path,
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
            "2",
        ],
    )
    api = (
        TestClient(create_app(manifest, source))
        .post(
            "/products/recover",
            json={
                "species_code": "SYN",
                "site_index": 5,
                "age": 2,
                "format": "taf",
            },
        )
        .json()
    )
    agent = (
        ToolBox(manifest, source)
        .recover_products({"species_code": "SYN", "site_index": 5, "age": 2, "format": "taf"})
        .as_dict()
    )
    web = TestClient(create_web_app(manifest, source)).get(
        "/ui/products", params={"species": "SYN", "site_index": 5, "age": 2}
    )
    assert web.status_code == 200
    assert "Mass balance" in web.text
    for payload in (service.as_dict(), cli, api, agent):
        result = _dict(payload["result"])
        totals = _dict(result["totals"])
        assert totals["lumber_2_or_better_bf_ha"] == 100.0
        checks = {str(_dict(check)["name"]): _dict(check) for check in _list(result["checks"])}
        assert checks["lumber_2_or_better_vs_graded"]["status"] == "pass"


def test_economics_parity_and_missing_price_gap(tmp_path: Path) -> None:
    """Economics values and missing-price gaps agree across interfaces."""
    source, manifest = _product_source(tmp_path)
    scenario = parse_scenario(_scenario())
    service = run_economics(manifest, source, scenario)
    scenario_path = tmp_path / "scenario.json"
    scenario_path.write_text(json.dumps(_scenario()), encoding="utf-8")
    cli = _cli_json(
        tmp_path,
        [
            "econ",
            "run",
            "--catalog",
            str(manifest),
            "--source",
            str(source),
            "--scenario",
            str(scenario_path),
        ],
    )
    client = TestClient(create_app(manifest, source))
    api = client.post("/economics/run", json=_scenario()).json()
    agent = ToolBox(manifest, source).run_economics(_scenario()).as_dict()
    web = TestClient(create_web_app(manifest, source)).get(
        "/ui/economics",
        params={
            "species": "SYN",
            "site_index": 5,
            "age": 2,
            "group": "lumber_2_or_better",
            "price": 1000,
            "unit": "CAD/mbf",
            "cost": 50,
            "discount_rate": 0.10,
        },
    )
    assert web.status_code == 200
    assert "NPV" in web.text
    for payload in (service.as_dict(), cli, api, agent):
        result = _dict(payload["result"])
        assert cast(float, result["npv_per_ha"]) == pytest.approx(32.6446, abs=1e-3)
        assert payload["evidence"] == "reimplemented"

    missing = _scenario(with_price=False)
    service_missing = run_economics(manifest, source, parse_scenario(missing))
    assert service_missing.result is not None
    assert service_missing.result["revenue_per_ha"] is None
    assert any(warning.code == "missing_price" for warning in service_missing.warnings)
    api_missing = client.post("/economics/run", json=missing).json()
    assert api_missing["result"]["revenue_per_ha"] is None
    assert api_missing["warnings"][0]["code"] == "missing_price"
    missing_path = tmp_path / "missing.json"
    missing_path.write_text(json.dumps(missing), encoding="utf-8")
    cli_missing = _cli_json(
        tmp_path,
        [
            "econ",
            "run",
            "--catalog",
            str(manifest),
            "--source",
            str(source),
            "--scenario",
            str(missing_path),
        ],
    )
    cli_warnings = _list(cli_missing["warnings"])
    assert _dict(cli_warnings[0])["code"] == "missing_price"
    agent_missing = ToolBox(manifest, source).run_economics(missing).as_dict()
    agent_warnings = _list(agent_missing["warnings"])
    assert _dict(agent_warnings[0])["code"] == "missing_price"
    web_missing = TestClient(create_web_app(manifest, source)).get(
        "/ui/economics",
        params={
            "species": "SYN",
            "site_index": 5,
            "age": 2,
            "group": "lumber_2_or_better",
            "discount_rate": 0.10,
        },
    )
    assert "missing_price" in web_missing.text


def test_interface_error_codes(tmp_path: Path) -> None:
    """Unsupported queries and missing assets are explicit across interfaces."""
    source, manifest = _product_source(tmp_path)
    client = TestClient(create_app(manifest, source))
    api = client.post(
        "/curves/query",
        json={"species_code": "NOPE", "site_index": 5, "age": 2},
    )
    assert api.status_code == 422
    assert api.json()["error"]["code"] == "query_failed"
    agent = ToolBox(manifest, source).query_curve(
        {"species_code": "NOPE", "site_index": 5, "age": 2}
    )
    assert agent.status == "error"
    assert agent.error is not None
    assert agent.error["code"] == "query_failed"
    web = TestClient(create_web_app(manifest, source)).get(
        "/ui/curve", params={"species": "NOPE", "site_index": 5, "age": 2}
    )
    assert web.status_code == 422
    assert "query_failed" in web.text
    runner = CliRunner()
    cli = runner.invoke(
        app,
        [
            "curve",
            "query",
            "--catalog",
            str(manifest),
            "--source",
            str(source),
            "--species",
            "NOPE",
            "--site-index",
            "5",
            "--age",
            "2",
        ],
    )
    assert cli.exit_code == 1
    missing = client.get("/provenance/missing")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "not_found"


def test_envelope_contract_has_all_keys(tmp_path: Path) -> None:
    """Every interface envelope carries the shared contract keys."""
    source, manifest = _product_source(tmp_path)
    service = query_curve(manifest, source, _query()).as_dict()
    api = TestClient(create_app(manifest, source)).get("/health").json()
    agent = ToolBox(manifest, source).search_catalog(species_code="SYN").as_dict()
    web = TestClient(create_web_app(manifest, source)).get("/ui")
    assert set(service) >= ENVELOPE_KEYS
    assert set(api) >= ENVELOPE_KEYS
    assert set(agent) >= ENVELOPE_KEYS
    assert web.status_code == 200
    assert "fresh-tipsy" in web.text
    assert "provenance" in web.text.lower()

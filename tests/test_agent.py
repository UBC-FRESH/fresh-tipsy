"""Tests for bounded assistant tools."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from fresh_tipsy.agent import SYSTEM_PROMPT, ToolBox, prompt, tool_specs
from fresh_tipsy.cli import app

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


def _toolbox(tmp_path: Path) -> ToolBox:
    """Build a tool box over the synthetic fixture."""
    return ToolBox(_manifest(tmp_path), FIXTURES)


def _query(*, table_format: str = "tab") -> dict[str, object]:
    """Return a synthetic query mapping."""
    return {
        "species_code": "SYN",
        "site_index": 5,
        "age": 2,
        "pnc": "N",
        "format": table_format,
    }


def _scenario() -> dict[str, object]:
    """Return a valid explicit scenario."""
    return {
        "query": _query(table_format="taf"),
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


def test_catalog_tools(tmp_path: Path) -> None:
    """Catalog search and table description preserve provenance."""
    tools = _toolbox(tmp_path)
    search = tools.search_catalog(species_code="SYN")
    assert search.status == "ok"
    assert search.result is not None
    assert search.result["count"] == 2
    tables = search.result["tables"]
    assert isinstance(tables, list)
    first = tables[0]
    assert isinstance(first, dict)
    asset_id = first["id"]
    detail = tools.describe_table(str(asset_id))
    assert detail.status == "ok"
    assert detail.result is not None
    assert detail.result["id"] == asset_id
    provenance = tools.get_provenance(str(asset_id))
    assert provenance.status == "ok"
    assert provenance.provenance is not None
    assert provenance.provenance["sha256"]


def test_curve_and_compare_tools(tmp_path: Path) -> None:
    """Curve tools return values and partial comparison errors."""
    tools = _toolbox(tmp_path)
    curve = tools.query_curve(_query())
    assert curve.status == "ok"
    assert curve.result is not None
    assert curve.result["height_site_m"] == 1.0
    assert curve.provenance is not None
    comparison = tools.compare_curves([_query(), {**_query(), "age": 3}])
    assert comparison.status == "ok"
    assert comparison.result is not None
    curves = comparison.result["curves"]
    assert isinstance(curves, list)
    assert len(curves) == 2
    partial = tools.compare_curves([_query(), {**_query(), "species_code": "NOPE"}])
    assert partial.status == "error"
    assert partial.error is not None
    assert partial.error["code"] == "comparison_partial"


def test_product_and_economics_tools(tmp_path: Path) -> None:
    """Product and economics tools use the shared service layer."""
    tools = _toolbox(tmp_path)
    product = tools.recover_products(_query(table_format="tab"))
    assert product.status == "ok"
    assert product.evidence == "model_output"
    economics = tools.run_economics(_scenario())
    assert economics.status == "ok"
    assert economics.result is not None
    assert economics.result["cost_per_ha"] == 50.0
    provenance = economics.result["provenance"]
    assert isinstance(provenance, dict)
    assert provenance["source_model"] == "TIPSY"


def test_tool_errors_are_structured(tmp_path: Path) -> None:
    """Tool failures return structured errors instead of invented data."""
    tools = _toolbox(tmp_path)
    missing = tools.describe_table("not-a-table")
    assert missing.status == "error"
    assert missing.error is not None
    assert missing.error["code"] == "not_found"
    bad_query = tools.query_curve({"species_code": "SYN"})
    assert bad_query.status == "error"
    assert bad_query.error is not None
    empty_compare = tools.compare_curves([])
    assert empty_compare.status == "error"
    assert empty_compare.error is not None
    empty = tools.search_catalog(pnc="Z")
    assert empty.status == "ok"
    assert empty.result is not None
    assert empty.result["count"] == 0


def test_tool_contract_and_prompt() -> None:
    """Tool specs and prompt preserve the provenance-first contract."""
    names = {spec["name"] for spec in tool_specs()}
    assert names == {
        "search_catalog",
        "describe_table",
        "query_curve",
        "compare_curves",
        "recover_products",
        "run_economics",
        "get_provenance",
    }
    assert "provenance" in SYSTEM_PROMPT.lower()
    assert "never invent" in SYSTEM_PROMPT.lower()
    assert "measured" in prompt().lower()

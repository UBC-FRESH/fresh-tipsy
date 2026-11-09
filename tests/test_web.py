"""Tests for the server-rendered web UI."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from fastapi.testclient import TestClient
from typer.testing import CliRunner

from fresh_tipsy.api.service import browse_catalog
from fresh_tipsy.cli import app
from fresh_tipsy.tables import CatalogQuery
from fresh_tipsy.web.app import create_web_app

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


def _client(tmp_path: Path) -> tuple[TestClient, Path]:
    """Build a web client and return it with the manifest."""
    manifest = _manifest(tmp_path)
    return TestClient(create_web_app(manifest, FIXTURES)), manifest


def _product_client(tmp_path: Path) -> TestClient:
    """Build a web client whose synthetic table has product values."""
    source = tmp_path / "product-source"
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
    out = tmp_path / "product-out"
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["db", "extract", "--source", str(source), "--out", str(out), "--json"],
    )
    assert result.exit_code == 0, result.output
    manifest = Path(json.loads(result.stdout)["manifest"])
    return TestClient(create_web_app(manifest, source))


def test_home_and_static(tmp_path: Path) -> None:
    """The home page and static stylesheet render."""
    client, _ = _client(tmp_path)
    response = client.get("/ui")
    assert response.status_code == 200
    assert "Fresh-style forest economics" in response.text
    assert "Curve explorer" in response.text
    root = client.get("/", follow_redirects=False)
    assert root.status_code in {302, 307}
    style = client.get("/static/style.css")
    assert style.status_code == 200
    assert "--accent" in style.text


def test_catalog_and_detail(tmp_path: Path) -> None:
    """Catalog search exposes source metadata and checksums."""
    client, manifest = _client(tmp_path)
    response = client.get("/ui/catalog", params={"species": "SYN", "site_index": 5})
    assert response.status_code == 200
    assert "SYN" in response.text
    assert "SHA-256" in response.text
    entries = browse_catalog(manifest, CatalogQuery(species_code="SYN")).result
    assert entries is not None
    tables = entries.get("tables")
    assert isinstance(tables, list)
    first = tables[0]
    assert isinstance(first, dict)
    asset_id = str(first["id"])
    detail = client.get(f"/ui/catalog/{asset_id}")
    assert detail.status_code == 200
    assert asset_id in detail.text
    assert "Citation" in detail.text
    missing = client.get("/ui/catalog/not-a-table")
    assert missing.status_code == 404
    assert "not_found" in missing.text


def test_curve_page(tmp_path: Path) -> None:
    """The curve explorer renders metrics and provenance."""
    client, _ = _client(tmp_path)
    response = client.get(
        "/ui/curve",
        params={"species": "SYN", "site_index": 5, "age": 2, "format": "tab"},
    )
    assert response.status_code == 200
    assert "Site height" in response.text
    assert "Request and provenance" in response.text
    assert "relative_path" in response.text


def test_product_page(tmp_path: Path) -> None:
    """The product view renders totals and mass-balance checks."""
    client = _product_client(tmp_path)
    response = client.get("/ui/products", params={"species": "SYN", "site_index": 5, "age": 2})
    assert response.status_code == 200
    assert "Product mix and residues" in response.text
    assert "Mass balance" in response.text
    assert "lumber_2_or_better_vs_graded" in response.text


def test_economics_page_and_missing_price(tmp_path: Path) -> None:
    """The economics view renders a result and exposes missing prices."""
    client, _ = _client(tmp_path)
    good = client.get(
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
            "period": "test",
        },
    )
    assert good.status_code == 200
    assert "NPV" in good.text
    assert "Request and provenance" in good.text
    product_client = _product_client(tmp_path)
    missing_price = product_client.get(
        "/ui/economics",
        params={
            "species": "SYN",
            "site_index": 5,
            "age": 2,
            "group": "lumber_2_or_better",
            "discount_rate": 0.10,
        },
    )
    assert missing_price.status_code == 200
    assert "missing_price" in missing_price.text


def test_ui_errors_are_visible(tmp_path: Path) -> None:
    """Unsupported queries and missing assumptions are visible, not hidden."""
    client, _ = _client(tmp_path)
    bad_curve = client.get(
        "/ui/curve",
        params={"species": "NOPE", "site_index": 5, "age": 2},
    )
    assert bad_curve.status_code == 422
    assert "query_failed" in bad_curve.text
    missing_discount = client.get(
        "/ui/economics",
        params={
            "species": "SYN",
            "site_index": 5,
            "age": 2,
            "group": "lumber_2_or_better",
            "price": 1000,
        },
    )
    assert missing_discount.status_code == 422
    assert "discount rate is required" in missing_discount.text


def test_empty_forms_and_not_configured() -> None:
    """Empty forms render without a catalog; data routes fail explicitly."""
    client = TestClient(create_web_app())
    missing = client.get("/ui/catalog")
    assert missing.status_code == 503
    assert "not_configured" in missing.text
    for path in ("/ui/curve", "/ui/products", "/ui/economics"):
        response = client.get(path)
        assert response.status_code == 200
        assert "Request and provenance" not in response.text


def test_product_error_and_residue_option(tmp_path: Path) -> None:
    """Product errors are visible and the residue option is honored."""
    client, _ = _client(tmp_path)
    bad = client.get("/ui/products", params={"species": "NOPE", "site_index": 5, "age": 2})
    assert bad.status_code == 422
    assert "product_failed" in bad.text
    result = client.get(
        "/ui/economics",
        params={
            "species": "SYN",
            "site_index": 5,
            "age": 2,
            "group": "lumber_2_or_better",
            "include_residues": "true",
            "price": 1000,
            "cost": 50,
            "discount_rate": 0.10,
        },
    )
    assert result.status_code == 200
    assert "NPV" in result.text

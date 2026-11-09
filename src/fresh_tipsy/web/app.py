"""Server-rendered FRESH-style web UI over the shared service layer."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

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
from fresh_tipsy.curves import CurveQuery
from fresh_tipsy.tables import CatalogQuery

_TEMPLATES = Path(__file__).parent / "templates"
_STATIC = Path(__file__).parent / "static"
_templates = Jinja2Templates(directory=str(_TEMPLATES))


def _render(
    request: Request,
    name: str,
    context: dict[str, object],
    status_code: int = 200,
) -> HTMLResponse:
    """Render a template.

    Parameters
    ----------
    request : Request
        Current HTTP request.
    name : str
        Template name.
    context : dict of str to object
        Template context.
    status_code : int, optional
        HTTP status. Defaults to 200.

    Returns
    -------
    HTMLResponse
        Rendered page.
    """
    return _templates.TemplateResponse(
        request=request,
        name=name,
        context=context,
        status_code=status_code,
    )


def _error_context(exc: ServiceError, form: dict[str, object]) -> dict[str, object]:
    """Build a template context for a service error."""
    return {
        "form": form,
        "error": {"code": exc.code, "message": str(exc)},
        "result": None,
        "request_data": None,
        "provenance": None,
        "warnings": [],
    }


def _catalog_path(app: FastAPI) -> Path:
    """Return the configured catalog or fail explicitly."""
    if app.state.catalog is None:
        raise ServiceError(
            "not_configured",
            "set FRESH_TIPSY_CATALOG or pass catalog to create_web_app",
            503,
        )
    return Path(app.state.catalog)


def _query_from_form(
    species: str,
    site_index: float,
    age: float,
    pnc: str | None,
    stock_height_m: float | None,
    table_format: str,
) -> CurveQuery:
    """Build a growth query from UI controls."""
    return CurveQuery(
        species_code=species,
        site_index=site_index,
        age=age,
        pnc=pnc,
        stock_height_m=stock_height_m,
        format=table_format,
    )


def _economics_scenario(
    *,
    species: str,
    site_index: float,
    age: float,
    pnc: str | None,
    stock_height_m: float | None,
    group: str,
    include_residues: bool,
    price: float | None,
    unit: str,
    cost: float | None,
    cost_category: str,
    discount_rate: float | None,
    price_period: str,
) -> dict[str, object]:
    """Build the explicit scenario mapping used by the service parser."""
    if discount_rate is None:
        raise ServiceError(
            "invalid_request",
            "discount rate is required for an economics scenario",
            422,
        )
    groups = [group]
    if include_residues:
        groups.append("residue")
    prices: list[dict[str, object]] = []
    if price is not None:
        prices.append(
            {
                "species_code": species,
                "group": group,
                "period": price_period,
                "price_per_unit": price,
                "unit": unit,
                "source": "web form input",
                "citation": "User-supplied web form input.",
            }
        )
    costs: list[dict[str, object]] = []
    if cost is not None:
        costs.append(
            {
                "category": cost_category,
                "age": 0.0,
                "amount_per_ha": cost,
                "label": "web form cost",
                "source": "web form input",
                "citation": "User-supplied web form input.",
            }
        )
    return {
        "query": {
            "species_code": species,
            "site_index": site_index,
            "age": age,
            "pnc": pnc,
            "stock_height_m": stock_height_m,
            "format": "taf",
        },
        "period": price_period,
        "revenue_groups": groups,
        "prices": prices,
        "costs": costs,
        "assumptions": {"discount_rate": discount_rate},
    }


def create_web_app(
    catalog: Path | None = None,
    source_root: Path | None = None,
) -> FastAPI:
    """Create the server-rendered web application.

    Parameters
    ----------
    catalog : Path or None, optional
        Manifest path. Falls back to ``FRESH_TIPSY_CATALOG``.
    source_root : Path or None, optional
        TIPSY install root.

    Returns
    -------
    FastAPI
        Web application.
    """
    application = FastAPI(
        title="fresh-tipsy web",
        version="0.1.0",
        docs_url=None,
        redoc_url=None,
    )
    configured = catalog
    if configured is None:
        env_catalog = os.environ.get("FRESH_TIPSY_CATALOG")
        configured = Path(env_catalog) if env_catalog else None
    application.state.catalog = configured
    application.state.source_root = source_root
    application.mount("/static", StaticFiles(directory=str(_STATIC)), name="static")

    @application.get("/", response_class=RedirectResponse)
    def root() -> RedirectResponse:
        """Redirect to the UI home."""
        return RedirectResponse(url="/ui")

    @application.get("/ui", response_class=HTMLResponse)
    def home(request: Request) -> HTMLResponse:
        """Render the UI home."""
        response = health()
        return _render(
            request,
            "home.html",
            {"result": response.as_dict(), "error": None},
        )

    @application.get("/ui/catalog", response_class=HTMLResponse)
    def catalog_page(
        request: Request,
        species: Annotated[str | None, Query()] = None,
        site_index: Annotated[float | None, Query()] = None,
        pnc: Annotated[str | None, Query()] = None,
        stock_height: Annotated[float | None, Query()] = None,
        source_version: Annotated[str | None, Query()] = None,
        table_format: Annotated[str | None, Query(alias="format")] = None,
        query_text: Annotated[str | None, Query(alias="q")] = None,
    ) -> HTMLResponse:
        """Render the catalog browser."""
        form: dict[str, object] = {
            "species": species,
            "site_index": site_index,
            "pnc": pnc,
            "stock_height": stock_height,
            "source_version": source_version,
            "format": table_format,
            "q": query_text,
        }
        try:
            response = browse_catalog(
                _catalog_path(application),
                CatalogQuery(
                    species_code=species,
                    site_index=site_index,
                    pnc=pnc,
                    stock_height_m=stock_height,
                    source_version=source_version,
                    format=table_format,
                    text=query_text,
                ),
            )
        except (ServiceError, ValueError) as exc:
            error = (
                exc
                if isinstance(exc, ServiceError)
                else ServiceError("invalid_request", str(exc), 422)
            )
            return _render(request, "catalog.html", _error_context(error, form), 422)
        return _render(
            request,
            "catalog.html",
            {
                "form": form,
                "result": response.result,
                "request_data": response.request,
                "provenance": response.provenance,
                "warnings": [warning.as_dict() for warning in response.warnings],
                "error": None,
            },
        )

    @application.get("/ui/catalog/{asset_id}", response_class=HTMLResponse)
    def table_page(request: Request, asset_id: str) -> HTMLResponse:
        """Render one catalog table and its provenance."""
        try:
            response = asset_provenance(_catalog_path(application), asset_id)
        except ServiceError as exc:
            return _render(
                request,
                "detail.html",
                _error_context(exc, {"asset_id": asset_id}),
                exc.status_code,
            )
        return _render(
            request,
            "detail.html",
            {
                "form": {"asset_id": asset_id},
                "result": response.result,
                "request_data": response.request,
                "provenance": response.provenance,
                "warnings": [warning.as_dict() for warning in response.warnings],
                "error": None,
            },
        )

    @application.get("/ui/curve", response_class=HTMLResponse)
    def curve_page(
        request: Request,
        species: Annotated[str | None, Query()] = None,
        site_index: Annotated[float | None, Query()] = None,
        age: Annotated[float | None, Query()] = None,
        pnc: Annotated[str | None, Query()] = None,
        stock_height: Annotated[float | None, Query()] = None,
        table_format: Annotated[str, Query(alias="format")] = "tab",
    ) -> HTMLResponse:
        """Render the curve explorer."""
        form: dict[str, object] = {
            "species": species,
            "site_index": site_index,
            "age": age,
            "pnc": pnc,
            "stock_height": stock_height,
            "format": table_format,
        }
        if species is None or site_index is None or age is None:
            return _render(
                request,
                "curve.html",
                {
                    "form": form,
                    "result": None,
                    "request_data": None,
                    "provenance": None,
                    "warnings": [],
                    "error": None,
                },
            )
        try:
            response = query_curve(
                _catalog_path(application),
                application.state.source_root,
                _query_from_form(species, site_index, age, pnc, stock_height, table_format),
            )
        except (ServiceError, ValueError) as exc:
            error = (
                exc
                if isinstance(exc, ServiceError)
                else ServiceError("invalid_request", str(exc), 422)
            )
            return _render(request, "curve.html", _error_context(error, form), 422)
        return _render(
            request,
            "curve.html",
            {
                "form": form,
                "result": response.result,
                "request_data": response.request,
                "provenance": response.provenance,
                "warnings": [warning.as_dict() for warning in response.warnings],
                "error": None,
            },
        )

    @application.get("/ui/products", response_class=HTMLResponse)
    def product_page(
        request: Request,
        species: Annotated[str | None, Query()] = None,
        site_index: Annotated[float | None, Query()] = None,
        age: Annotated[float | None, Query()] = None,
        pnc: Annotated[str | None, Query()] = None,
        stock_height: Annotated[float | None, Query()] = None,
    ) -> HTMLResponse:
        """Render the product mix and residue view."""
        form: dict[str, object] = {
            "species": species,
            "site_index": site_index,
            "age": age,
            "pnc": pnc,
            "stock_height": stock_height,
        }
        if species is None or site_index is None or age is None:
            return _render(
                request,
                "product.html",
                {
                    "form": form,
                    "result": None,
                    "request_data": None,
                    "provenance": None,
                    "warnings": [],
                    "error": None,
                },
            )
        try:
            response = recover_products(
                _catalog_path(application),
                application.state.source_root,
                _query_from_form(species, site_index, age, pnc, stock_height, "taf"),
            )
        except (ServiceError, ValueError) as exc:
            error = (
                exc
                if isinstance(exc, ServiceError)
                else ServiceError("invalid_request", str(exc), 422)
            )
            return _render(request, "product.html", _error_context(error, form), 422)
        return _render(
            request,
            "product.html",
            {
                "form": form,
                "result": response.result,
                "request_data": response.request,
                "provenance": response.provenance,
                "warnings": [warning.as_dict() for warning in response.warnings],
                "error": None,
            },
        )

    @application.get("/ui/economics", response_class=HTMLResponse)
    def economics_page(
        request: Request,
        species: Annotated[str | None, Query()] = None,
        site_index: Annotated[float | None, Query()] = None,
        age: Annotated[float | None, Query()] = None,
        pnc: Annotated[str | None, Query()] = None,
        stock_height: Annotated[float | None, Query()] = None,
        group: Annotated[str, Query()] = "lumber_2_or_better",
        include_residues: Annotated[bool, Query()] = False,
        price: Annotated[float | None, Query()] = None,
        unit: Annotated[str, Query()] = "CAD/mbf",
        cost: Annotated[float | None, Query()] = None,
        cost_category: Annotated[str, Query()] = "regeneration",
        discount_rate: Annotated[float | None, Query()] = None,
        period: Annotated[str, Query()] = "web",
    ) -> HTMLResponse:
        """Render the economics scenario builder."""
        form: dict[str, object] = {
            "species": species,
            "site_index": site_index,
            "age": age,
            "pnc": pnc,
            "stock_height": stock_height,
            "group": group,
            "include_residues": include_residues,
            "price": price,
            "unit": unit,
            "cost": cost,
            "cost_category": cost_category,
            "discount_rate": discount_rate,
            "period": period,
        }
        if species is None or site_index is None or age is None:
            return _render(
                request,
                "economics.html",
                {
                    "form": form,
                    "result": None,
                    "request_data": None,
                    "provenance": None,
                    "warnings": [],
                    "error": None,
                },
            )
        try:
            response = run_economics(
                _catalog_path(application),
                application.state.source_root,
                parse_scenario(
                    _economics_scenario(
                        species=species,
                        site_index=site_index,
                        age=age,
                        pnc=pnc,
                        stock_height_m=stock_height,
                        group=group,
                        include_residues=include_residues,
                        price=price,
                        unit=unit,
                        cost=cost,
                        cost_category=cost_category,
                        discount_rate=discount_rate,
                        price_period=period,
                    )
                ),
            )
        except (ServiceError, ValueError) as exc:
            error = (
                exc
                if isinstance(exc, ServiceError)
                else ServiceError("invalid_request", str(exc), 422)
            )
            return _render(request, "economics.html", _error_context(error, form), 422)
        return _render(
            request,
            "economics.html",
            {
                "form": form,
                "result": response.result,
                "request_data": response.request,
                "provenance": response.provenance,
                "warnings": [warning.as_dict() for warning in response.warnings],
                "error": None,
            },
        )

    return application


app = create_web_app()

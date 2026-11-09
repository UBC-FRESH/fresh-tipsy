"""FastAPI application over the shared fresh-tipsy service layer."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from fresh_tipsy.api.models import (
    CurveQueryRequest,
    EconomicsScenarioRequest,
    ServiceEnvelopeModel,
    ServiceErrorEnvelope,
)
from fresh_tipsy.api.service import (
    ServiceError,
    ServiceIssue,
    asset_provenance,
    browse_catalog,
    health,
    parse_scenario,
    query_curve,
    recover_products,
    run_economics,
)
from fresh_tipsy.tables import CatalogQuery


def _error_response(
    request: dict[str, object], issue: ServiceIssue, status_code: int
) -> JSONResponse:
    """Build a structured error response.

    Parameters
    ----------
    request : dict of str to object
        Original request context.
    issue : ServiceIssue
        Structured issue.
    status_code : int
        HTTP status.

    Returns
    -------
    JSONResponse
        Error envelope.
    """
    body = ServiceErrorEnvelope.from_issue(request, issue).model_dump()
    return JSONResponse(status_code=status_code, content=body)


def create_app(
    catalog: Path | None = None,
    source_root: Path | None = None,
) -> FastAPI:
    """Create the FastAPI application.

    Parameters
    ----------
    catalog : Path or None, optional
        Manifest path. Falls back to ``FRESH_TIPSY_CATALOG``.
    source_root : Path or None, optional
        TIPSY install root used to resolve table paths.

    Returns
    -------
    FastAPI
        Application.
    """
    application = FastAPI(
        title="fresh-tipsy",
        version="0.1.0",
        description="Provenance-first TIPSY product and economics service.",
    )
    configured = catalog
    if configured is None:
        env_catalog = os.environ.get("FRESH_TIPSY_CATALOG")
        configured = Path(env_catalog) if env_catalog else None
    application.state.catalog = configured
    application.state.source_root = source_root

    def _catalog_path() -> Path:
        """Return the configured catalog or fail explicitly."""
        if application.state.catalog is None:
            raise ServiceError(
                "not_configured",
                "set FRESH_TIPSY_CATALOG or pass catalog to create_app",
                503,
            )
        return Path(application.state.catalog)

    @application.exception_handler(ServiceError)
    async def _handle_service_error(request: Request, exc: ServiceError) -> JSONResponse:
        """Map a service error to a structured HTTP response."""
        return _error_response(
            {"path": request.url.path},
            ServiceIssue(exc.code, str(exc)),
            exc.status_code,
        )

    @application.exception_handler(RequestValidationError)
    async def _handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Map a request-validation error to a structured response."""
        message = "; ".join(
            f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
            for error in exc.errors()
        )
        return _error_response(
            {"path": request.url.path},
            ServiceIssue("invalid_request", message),
            422,
        )

    @application.get("/health", response_model=ServiceEnvelopeModel)
    def health_endpoint() -> ServiceEnvelopeModel:
        """Return service health."""
        return ServiceEnvelopeModel.from_response(health())

    @application.get("/catalog", response_model=ServiceEnvelopeModel)
    def catalog_endpoint(
        species: Annotated[str | None, Query()] = None,
        site_index: Annotated[float | None, Query()] = None,
        pnc: Annotated[str | None, Query()] = None,
        stock_height: Annotated[float | None, Query()] = None,
        source_version: Annotated[str | None, Query()] = None,
        table_format: Annotated[str | None, Query(alias="format")] = None,
        text: Annotated[str | None, Query()] = None,
    ) -> ServiceEnvelopeModel:
        """Browse the table catalog."""
        try:
            query = CatalogQuery(
                species_code=species,
                site_index=site_index,
                pnc=pnc,
                stock_height_m=stock_height,
                source_version=source_version,
                format=table_format,
                text=text,
            )
        except ValueError as exc:
            raise ServiceError("invalid_request", str(exc), 422) from exc
        response = browse_catalog(_catalog_path(), query)
        return ServiceEnvelopeModel.from_response(response)

    @application.get("/catalog/{table_id}", response_model=ServiceEnvelopeModel)
    def table_endpoint(table_id: str) -> ServiceEnvelopeModel:
        """Return one catalog table and its provenance."""
        return ServiceEnvelopeModel.from_response(asset_provenance(_catalog_path(), table_id))

    @application.post("/curves/query", response_model=ServiceEnvelopeModel)
    def curve_endpoint(request: CurveQueryRequest) -> ServiceEnvelopeModel:
        """Query a growth curve."""
        try:
            query = request.to_query()
        except ValueError as exc:
            raise ServiceError("invalid_request", str(exc), 422) from exc
        response = query_curve(_catalog_path(), application.state.source_root, query)
        return ServiceEnvelopeModel.from_response(response)

    @application.post("/products/recover", response_model=ServiceEnvelopeModel)
    def product_endpoint(request: CurveQueryRequest) -> ServiceEnvelopeModel:
        """Recover products from a `.taf` table."""
        try:
            query = request.to_query()
        except ValueError as exc:
            raise ServiceError("invalid_request", str(exc), 422) from exc
        response = recover_products(_catalog_path(), application.state.source_root, query)
        return ServiceEnvelopeModel.from_response(response)

    @application.post("/economics/run", response_model=ServiceEnvelopeModel)
    def economics_endpoint(request: EconomicsScenarioRequest) -> ServiceEnvelopeModel:
        """Run an explicit economics scenario."""
        scenario = parse_scenario(request.as_dict())
        response = run_economics(_catalog_path(), application.state.source_root, scenario)
        return ServiceEnvelopeModel.from_response(response)

    @application.get("/provenance/{asset_id}", response_model=ServiceEnvelopeModel)
    def provenance_endpoint(asset_id: str) -> ServiceEnvelopeModel:
        """Return one asset and its provenance."""
        return ServiceEnvelopeModel.from_response(asset_provenance(_catalog_path(), asset_id))

    return application


app = create_app()

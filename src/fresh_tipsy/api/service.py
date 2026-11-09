"""Shared typed service layer for CLI, API, web, and assistant interfaces."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from fresh_tipsy.curves import CurveEngine, CurvePoint, CurveQuery
from fresh_tipsy.economics import (
    CostCategory,
    CostEntry,
    DiscountAssumptions,
    EconomicResult,
    EconomicsRequest,
    PriceBook,
    PriceEntry,
    PriceKey,
    evaluate_economics,
)
from fresh_tipsy.products import ProductGroup, ProductRecovery
from fresh_tipsy.tables import CatalogQuery, TableCatalog


@dataclass(frozen=True)
class ServiceIssue:
    """A structured service error or warning.

    Parameters
    ----------
    code : str
        Stable issue code.
    message : str
        Human-readable explanation.
    """

    code: str
    message: str

    def as_dict(self) -> dict[str, str]:
        """Return a JSON-ready issue.

        Returns
        -------
        dict of str to str
            Issue fields.
        """
        return {"code": self.code, "message": self.message}


@dataclass(frozen=True)
class ServiceResponse:
    """Shared response envelope.

    Parameters
    ----------
    status : str
        ``"ok"`` or ``"error"``.
    request : dict of str to object
        Original request inputs.
    result : dict of str to object or None
        Typed result payload.
    provenance : dict of str to object or None
        Primary source provenance.
    evidence : str or None
        Primary evidence label.
    warnings : tuple of ServiceIssue
        Non-fatal gaps or warnings.
    error : ServiceIssue or None
        Fatal error, when ``status`` is ``"error"``.
    """

    status: str
    request: dict[str, object]
    result: dict[str, object] | None
    provenance: dict[str, object] | None
    evidence: str | None
    warnings: tuple[ServiceIssue, ...] = ()
    error: ServiceIssue | None = None

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-ready response envelope.

        Returns
        -------
        dict of str to object
            Envelope fields.
        """
        return {
            "status": self.status,
            "request": self.request,
            "result": self.result,
            "provenance": self.provenance,
            "evidence": self.evidence,
            "warnings": [warning.as_dict() for warning in self.warnings],
            "error": None if self.error is None else self.error.as_dict(),
        }


class ServiceError(ValueError):
    """A service failure with an HTTP-compatible status code.

    Parameters
    ----------
    code : str
        Stable error code.
    message : str
        Human-readable explanation.
    status_code : int, optional
        HTTP status code. Defaults to 400.
    """

    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code


@dataclass(frozen=True)
class EconomicsScenario:
    """Typed economics scenario shared by the CLI and API.

    Parameters
    ----------
    query : CurveQuery
        Product query.
    period : str
        Price period.
    revenue_groups : tuple of ProductGroup
        Selected revenue groups.
    prices : tuple of PriceEntry
        Explicit prices.
    costs : tuple of CostEntry
        Explicit costs.
    assumptions : DiscountAssumptions
        Discount assumptions.
    """

    query: CurveQuery
    period: str
    revenue_groups: tuple[ProductGroup, ...]
    prices: tuple[PriceEntry, ...]
    costs: tuple[CostEntry, ...]
    assumptions: DiscountAssumptions

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-ready scenario.

        Returns
        -------
        dict of str to object
            Scenario fields.
        """
        return {
            "query": query_payload(self.query),
            "period": self.period,
            "revenue_groups": [group.value for group in self.revenue_groups],
            "prices": [price.as_dict() for price in self.prices],
            "costs": [cost.as_dict() for cost in self.costs],
            "assumptions": self.assumptions.as_dict(),
        }


def query_payload(query: CurveQuery) -> dict[str, object]:
    """Return the query portion of a service request.

    Parameters
    ----------
    query : CurveQuery
        Growth query.

    Returns
    -------
    dict of str to object
        Query inputs.
    """
    return {
        "species_code": query.species_code,
        "site_index": query.site_index,
        "age": query.age,
        "pnc": query.pnc,
        "stock_height_m": query.stock_height_m,
        "source_version": query.source_version,
        "scenario": query.scenario,
        "initial_density": query.initial_density,
        "pct_density": query.pct_density,
        "ct_density": query.ct_density,
        "format": query.format,
    }


def _source_root(source: Path | None) -> Path:
    """Resolve a source root.

    Parameters
    ----------
    source : Path or None
        Explicit install root.

    Returns
    -------
    Path
        Source root.

    Raises
    ------
    ServiceError
        When no source root is available.
    """
    if source is not None:
        return source
    configured = os.environ.get("TIPSY_INSTALL")
    if configured:
        return Path(configured)
    raise ServiceError(
        "source_unavailable",
        "--source is required unless TIPSY_INSTALL is set",
        503,
    )


def _engine(catalog: Path, source: Path | None) -> CurveEngine:
    """Build a curve engine from a manifest.

    Parameters
    ----------
    catalog : Path
        Manifest path.
    source : Path or None
        Source install root.

    Returns
    -------
    CurveEngine
        Engine backed by the manifest.

    Raises
    ------
    ServiceError
        When the manifest or source is unavailable.
    """
    if not catalog.is_file():
        raise ServiceError("catalog_missing", f"manifest does not exist: {catalog}", 404)
    try:
        return CurveEngine.from_manifest(catalog, source_root=_source_root(source))
    except (ValueError, OSError) as exc:
        raise ServiceError("catalog_invalid", str(exc), 422) from exc


def _catalog(catalog: Path) -> TableCatalog:
    """Load a table catalog.

    Parameters
    ----------
    catalog : Path
        Manifest path.

    Returns
    -------
    TableCatalog
        Loaded catalog.

    Raises
    ------
    ServiceError
        When the manifest is missing or invalid.
    """
    if not catalog.is_file():
        raise ServiceError("catalog_missing", f"manifest does not exist: {catalog}", 404)
    try:
        return TableCatalog.from_manifest(catalog)
    except (ValueError, OSError) as exc:
        raise ServiceError("catalog_invalid", str(exc), 422) from exc


def _curve_response(
    request: dict[str, object],
    point: CurvePoint,
) -> ServiceResponse:
    """Build a success envelope for a curve point."""
    warnings = tuple(
        ServiceIssue("unavailable_metric", metric) for metric in point.unavailable_metrics
    )
    return ServiceResponse(
        status="ok",
        request=request,
        result=point.as_dict(),
        provenance=point.provenance.as_dict(),
        evidence=point.provenance.evidence,
        warnings=warnings,
    )


def query_curve(
    catalog: Path,
    source: Path | None,
    query: CurveQuery,
) -> ServiceResponse:
    """Query a curve through the shared service layer.

    Parameters
    ----------
    catalog : Path
        Manifest path.
    source : Path or None
        Source install root.
    query : CurveQuery
        Growth query.

    Returns
    -------
    ServiceResponse
        Shared envelope.

    Raises
    ------
    ServiceError
        When the query cannot be answered.
    """
    try:
        point = _engine(catalog, source).point(query)
    except ServiceError:
        raise
    except (ValueError, OSError) as exc:
        raise ServiceError("query_failed", str(exc), 422) from exc
    return _curve_response({"query": query_payload(query)}, point)


def _product_response(
    request: dict[str, object],
    recovery: ProductRecovery,
) -> ServiceResponse:
    """Build a success envelope for product recovery."""
    warnings = tuple(
        ServiceIssue("mass_balance_unavailable", f"{check.name}: {check.status}")
        for check in recovery.checks
        if check.status != "pass"
    )
    return ServiceResponse(
        status="ok",
        request=request,
        result=recovery.as_dict(),
        provenance=recovery.provenance.as_dict(),
        evidence="model_output",
        warnings=warnings,
    )


def recover_products(
    catalog: Path,
    source: Path | None,
    query: CurveQuery,
) -> ServiceResponse:
    """Recover products through the shared service layer.

    Parameters
    ----------
    catalog : Path
        Manifest path.
    source : Path or None
        Source install root.
    query : CurveQuery
        Product query. The selected format must be ``taf``.

    Returns
    -------
    ServiceResponse
        Shared envelope.

    Raises
    ------
    ServiceError
        When the query or source cannot be answered.
    """
    try:
        recovery = _engine(catalog, source).products(query)
    except ServiceError:
        raise
    except (ValueError, OSError) as exc:
        raise ServiceError("product_failed", str(exc), 422) from exc
    return _product_response({"query": query_payload(query)}, recovery)


def _economics_response(
    request: dict[str, object],
    result: EconomicResult,
) -> ServiceResponse:
    """Build a success envelope for economics."""
    return ServiceResponse(
        status="ok",
        request=request,
        result=result.as_dict(),
        provenance={
            "source_model": result.source_model,
            "source_version": result.source_version,
            "relative_path": result.source_relative_path,
            "sha256": result.source_sha256,
            "citation": result.source_citation,
        },
        evidence=result.evidence,
        warnings=tuple(ServiceIssue(gap.code, gap.message) for gap in result.gaps),
    )


def run_economics(
    catalog: Path,
    source: Path | None,
    scenario: EconomicsScenario,
) -> ServiceResponse:
    """Evaluate an explicit economics scenario.

    Parameters
    ----------
    catalog : Path
        Manifest path.
    source : Path or None
        Source install root.
    scenario : EconomicsScenario
        Typed scenario.

    Returns
    -------
    ServiceResponse
        Shared envelope.

    Raises
    ------
    ServiceError
        When the scenario cannot be evaluated.
    """
    try:
        recovery = _engine(catalog, source).products(scenario.query)
        request = EconomicsRequest(
            recovery=recovery,
            price_book=PriceBook(scenario.prices),
            assumptions=scenario.assumptions,
            revenue_groups=scenario.revenue_groups,
            costs=scenario.costs,
            period=scenario.period,
        )
        result = evaluate_economics(request)
    except ServiceError:
        raise
    except (ValueError, OSError) as exc:
        raise ServiceError("economics_failed", str(exc), 422) from exc
    return _economics_response({"scenario": scenario.as_dict()}, result)


def browse_catalog(catalog: Path, query: CatalogQuery) -> ServiceResponse:
    """Search the table catalog.

    Parameters
    ----------
    catalog : Path
        Manifest path.
    query : CatalogQuery
        Catalog filters.

    Returns
    -------
    ServiceResponse
        Shared envelope.

    Raises
    ------
    ServiceError
        When the catalog cannot be loaded.
    """
    entries = _catalog(catalog).search(query)
    request: dict[str, object] = {
        "species_code": query.species_code,
        "site_index": query.site_index,
        "pnc": query.pnc,
        "stock_height_m": query.stock_height_m,
        "source_version": query.source_version,
        "format": query.format,
        "text": query.text,
    }
    return ServiceResponse(
        status="ok",
        request=request,
        result={"count": len(entries), "tables": [entry.as_dict() for entry in entries]},
        provenance=None,
        evidence="source_table",
    )


def asset_provenance(catalog: Path, asset_id: str) -> ServiceResponse:
    """Return one catalog asset and its provenance.

    Parameters
    ----------
    catalog : Path
        Manifest path.
    asset_id : str
        Stable asset ID.

    Returns
    -------
    ServiceResponse
        Shared envelope.

    Raises
    ------
    ServiceError
        When the asset is missing.
    """
    table_catalog = _catalog(catalog)
    entry = next(
        (candidate for candidate in table_catalog.entries if candidate.asset_id == asset_id),
        None,
    )
    if entry is None:
        raise ServiceError("not_found", f"asset not found: {asset_id}", 404)
    payload = entry.as_dict()
    return ServiceResponse(
        status="ok",
        request={"asset_id": asset_id},
        result=payload,
        provenance={
            "asset_id": entry.asset_id,
            "relative_path": entry.relative_path,
            "sha256": entry.sha256,
            "source_model": entry.source_model,
            "source_version": entry.source_version,
            "citation": entry.citation,
        },
        evidence=entry.evidence,
    )


def health() -> ServiceResponse:
    """Return service health.

    Returns
    -------
    ServiceResponse
        Healthy envelope.
    """
    return ServiceResponse(
        status="ok",
        request={},
        result={"status": "ok"},
        provenance=None,
        evidence=None,
    )


def _optional_float(data: dict[str, object], key: str) -> float | None:
    """Read an optional numeric scenario field."""
    value = data.get(key)
    return None if value is None else float(str(value))


def _optional_int(data: dict[str, object], key: str) -> int | None:
    """Read an optional integer scenario field."""
    value = data.get(key)
    return None if value is None else int(float(str(value)))


def parse_curve_query(data: dict[str, object]) -> CurveQuery:
    """Parse a growth query mapping.

    Parameters
    ----------
    data : dict of str to object
        Query fields.

    Returns
    -------
    CurveQuery
        Growth query.

    Raises
    ------
    ServiceError
        When the query is malformed.
    """
    try:
        return CurveQuery(
            species_code=str(data["species_code"]),
            site_index=float(str(data["site_index"])),
            age=float(str(data["age"])),
            pnc=None if data.get("pnc") is None else str(data["pnc"]),
            stock_height_m=_optional_float(data, "stock_height_m"),
            source_version=(
                None if data.get("source_version") is None else str(data["source_version"])
            ),
            scenario=None if data.get("scenario") is None else str(data["scenario"]),
            initial_density=_optional_int(data, "initial_density"),
            pct_density=_optional_int(data, "pct_density"),
            ct_density=_optional_int(data, "ct_density"),
            format=str(data.get("format", "taf")),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ServiceError("invalid_request", f"invalid scenario.query: {exc}", 422) from exc


def _scenario_query(data: dict[str, object]) -> CurveQuery:
    """Build a curve query from scenario data.

    Parameters
    ----------
    data : dict of str to object
        Scenario object.

    Returns
    -------
    CurveQuery
        Growth query.

    Raises
    ------
    ServiceError
        When the query is malformed.
    """
    raw = data.get("query")
    if not isinstance(raw, dict):
        raise ServiceError("invalid_request", "scenario.query must be an object", 422)
    return parse_curve_query(raw)


def parse_scenario(data: dict[str, object]) -> EconomicsScenario:
    """Parse a shared economics scenario.

    Parameters
    ----------
    data : dict of str to object
        Scenario object.

    Returns
    -------
    EconomicsScenario
        Typed scenario.

    Raises
    ------
    ServiceError
        When the scenario is malformed.
    """
    query = _scenario_query(data)
    period = str(data.get("period", "default"))
    raw_groups = data.get("revenue_groups")
    if not isinstance(raw_groups, list) or not raw_groups:
        raise ServiceError(
            "invalid_request", "scenario.revenue_groups must be a non-empty list", 422
        )
    try:
        groups = tuple(ProductGroup(str(group)) for group in raw_groups)
    except ValueError as exc:
        raise ServiceError(
            "invalid_request", f"invalid scenario.revenue_groups: {exc}", 422
        ) from exc
    raw_prices = data.get("prices", [])
    if not isinstance(raw_prices, list):
        raise ServiceError("invalid_request", "scenario.prices must be a list", 422)
    prices: list[PriceEntry] = []
    for index, raw_price in enumerate(raw_prices):
        if not isinstance(raw_price, dict):
            raise ServiceError(
                "invalid_request", f"scenario.prices[{index}] must be an object", 422
            )
        key_data = raw_price.get("key", raw_price)
        if not isinstance(key_data, dict):
            raise ServiceError(
                "invalid_request",
                f"scenario.prices[{index}].key must be an object",
                422,
            )
        try:
            prices.append(
                PriceEntry(
                    key=PriceKey(
                        species_code=str(key_data.get("species_code", query.species_code)),
                        group=ProductGroup(str(key_data["group"])),
                        period=str(key_data.get("period", period)),
                        grade=(None if key_data.get("grade") is None else str(key_data["grade"])),
                        dimension=(
                            None
                            if key_data.get("dimension") is None
                            else str(key_data["dimension"])
                        ),
                        detail=(
                            None if key_data.get("detail") is None else str(key_data["detail"])
                        ),
                    ),
                    price_per_unit=float(raw_price["price_per_unit"]),
                    unit=str(raw_price["unit"]),
                    source=str(raw_price.get("source", "scenario")),
                    citation=str(raw_price.get("citation", "Scenario input.")),
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ServiceError(
                "invalid_request", f"invalid scenario.prices[{index}]: {exc}", 422
            ) from exc
    raw_costs = data.get("costs", [])
    if not isinstance(raw_costs, list):
        raise ServiceError("invalid_request", "scenario.costs must be a list", 422)
    costs: list[CostEntry] = []
    for index, raw_cost in enumerate(raw_costs):
        if not isinstance(raw_cost, dict):
            raise ServiceError("invalid_request", f"scenario.costs[{index}] must be an object", 422)
        try:
            costs.append(
                CostEntry(
                    category=CostCategory(str(raw_cost["category"])),
                    age=float(raw_cost["age"]),
                    amount_per_ha=float(raw_cost["amount_per_ha"]),
                    label=str(raw_cost["label"]),
                    source=str(raw_cost.get("source", "scenario")),
                    citation=str(raw_cost.get("citation", "Scenario input.")),
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ServiceError(
                "invalid_request", f"invalid scenario.costs[{index}]: {exc}", 422
            ) from exc
    raw_assumptions = data.get("assumptions")
    if not isinstance(raw_assumptions, dict):
        raise ServiceError("invalid_request", "scenario.assumptions must be an object", 422)
    try:
        assumptions = DiscountAssumptions(
            discount_rate=float(raw_assumptions["discount_rate"]),
            real_price_increase=float(raw_assumptions.get("real_price_increase", 0.0)),
            real_cost_increase=float(raw_assumptions.get("real_cost_increase", 0.0)),
            real_increase_duration=float(raw_assumptions.get("real_increase_duration", 25.0)),
            base_age=float(raw_assumptions.get("base_age", 0.0)),
            include_sunk_costs=bool(raw_assumptions.get("include_sunk_costs", False)),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ServiceError("invalid_request", f"invalid scenario.assumptions: {exc}", 422) from exc
    try:
        return EconomicsScenario(
            query=query,
            period=period,
            revenue_groups=groups,
            prices=tuple(prices),
            costs=tuple(costs),
            assumptions=assumptions,
        )
    except ValueError as exc:
        raise ServiceError("invalid_request", f"invalid scenario: {exc}", 422) from exc

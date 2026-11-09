"""Bounded assistant tools over the shared fresh-tipsy service layer."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from fresh_tipsy.api.service import (
    ServiceError,
    ServiceIssue,
    ServiceResponse,
    asset_provenance,
    browse_catalog,
    parse_curve_query,
    parse_scenario,
    query_curve,
    recover_products,
    run_economics,
)
from fresh_tipsy.tables import CatalogQuery


@dataclass(frozen=True)
class ToolResult:
    """A provenance-preserving tool result.

    Parameters
    ----------
    tool : str
        Tool name.
    status : str
        ``"ok"`` or ``"error"``.
    request : dict of str to object
        Tool inputs.
    result : dict of str to object or None
        Tool result.
    provenance : dict of str to object or None
        Primary source provenance.
    evidence : str or None
        Primary evidence label.
    warnings : tuple of dict
        Non-fatal gaps.
    error : dict of str to str or None
        Structured error.
    """

    tool: str
    status: str
    request: dict[str, object]
    result: dict[str, object] | None
    provenance: dict[str, object] | None
    evidence: str | None
    warnings: tuple[dict[str, str], ...] = ()
    error: dict[str, str] | None = None

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-ready tool result.

        Returns
        -------
        dict of str to object
            Result fields.
        """
        return {
            "tool": self.tool,
            "status": self.status,
            "request": self.request,
            "result": self.result,
            "provenance": self.provenance,
            "evidence": self.evidence,
            "warnings": list(self.warnings),
            "error": self.error,
        }


def _from_response(tool: str, response: ServiceResponse) -> ToolResult:
    """Convert a service response to a tool result."""
    return ToolResult(
        tool=tool,
        status=response.status,
        request=response.request,
        result=response.result,
        provenance=response.provenance,
        evidence=response.evidence,
        warnings=tuple(warning.as_dict() for warning in response.warnings),
        error=None if response.error is None else response.error.as_dict(),
    )


def _from_error(tool: str, request: dict[str, object], error: Exception) -> ToolResult:
    """Convert an exception to a structured tool error."""
    if isinstance(error, ServiceError):
        issue = ServiceIssue(error.code, str(error))
    else:
        issue = ServiceIssue("invalid_request", str(error))
    return ToolResult(
        tool=tool,
        status="error",
        request=request,
        result=None,
        provenance=None,
        evidence=None,
        error=issue.as_dict(),
    )


@dataclass(frozen=True)
class ToolBox:
    """Deterministic assistant tools for one catalog.

    Parameters
    ----------
    catalog : Path
        Manifest path.
    source_root : Path or None, optional
        TIPSY install root.
    """

    catalog: Path
    source_root: Path | None = None

    def _call(
        self,
        tool: str,
        request: dict[str, object],
        function: Callable[[], ServiceResponse],
    ) -> ToolResult:
        """Run one service call and wrap its result."""
        try:
            return _from_response(tool, function())
        except (ServiceError, ValueError, OSError) as exc:
            return _from_error(tool, request, exc)

    def search_catalog(
        self,
        query: str | None = None,
        *,
        species_code: str | None = None,
        site_index: float | None = None,
        pnc: str | None = None,
        stock_height_m: float | None = None,
        source_version: str | None = None,
        table_format: str | None = None,
    ) -> ToolResult:
        """Search the catalog.

        Parameters
        ----------
        query : str or None, optional
            Free-text search.
        species_code : str or None, optional
            Species filter.
        site_index : float or None, optional
            Site index filter.
        pnc : str or None, optional
            PNC filter.
        stock_height_m : float or None, optional
            Stock-height filter.
        source_version : str or None, optional
            Source-version filter.
        table_format : str or None, optional
            Source format filter.

        Returns
        -------
        ToolResult
            Matching tables and provenance.
        """
        request: dict[str, object] = {
            "query": query,
            "species_code": species_code,
            "site_index": site_index,
            "pnc": pnc,
            "stock_height_m": stock_height_m,
            "source_version": source_version,
            "format": table_format,
        }
        try:
            catalog_query = CatalogQuery(
                species_code=species_code,
                site_index=site_index,
                pnc=pnc,
                stock_height_m=stock_height_m,
                source_version=source_version,
                format=table_format,
                text=query,
            )
        except ValueError as exc:
            return _from_error("search_catalog", request, exc)
        return self._call(
            "search_catalog",
            request,
            lambda: browse_catalog(self.catalog, catalog_query),
        )

    def describe_table(self, asset_id: str) -> ToolResult:
        """Describe one catalog table.

        Parameters
        ----------
        asset_id : str
            Stable asset ID.

        Returns
        -------
        ToolResult
            Table metadata and provenance.
        """
        request: dict[str, object] = {"asset_id": asset_id}
        return self._call(
            "describe_table",
            request,
            lambda: asset_provenance(self.catalog, asset_id),
        )

    def query_curve(self, query: dict[str, object]) -> ToolResult:
        """Query one growth curve.

        Parameters
        ----------
        query : dict of str to object
            Query fields.

        Returns
        -------
        ToolResult
            Curve result with provenance.
        """
        try:
            parsed = parse_curve_query(query)
        except ServiceError as exc:
            return _from_error("query_curve", {"query": query}, exc)
        return self._call(
            "query_curve",
            {"query": query},
            lambda: service_query_curve(self.catalog, self.source_root, parsed),
        )

    def compare_curves(self, queries: list[dict[str, object]]) -> ToolResult:
        """Compare several growth curves.

        Parameters
        ----------
        queries : list of dict
            Query mappings.

        Returns
        -------
        ToolResult
            One result per query; errors are embedded in the list.
        """
        request: dict[str, object] = {"queries": queries}
        if not queries:
            return _from_error(
                "compare_curves",
                request,
                ServiceError("invalid_request", "at least one query is required", 422),
            )
        results = [self.query_curve(query).as_dict() for query in queries]
        errors = [result for result in results if result["status"] == "error"]
        error = None
        if errors:
            error = {
                "code": "comparison_partial",
                "message": f"{len(errors)} of {len(results)} queries failed",
            }
        return ToolResult(
            tool="compare_curves",
            status="error" if errors else "ok",
            request=request,
            result={"curves": results},
            provenance=None,
            evidence=None,
            error=error,
        )

    def recover_products(self, query: dict[str, object]) -> ToolResult:
        """Recover products for one `.taf` query.

        Parameters
        ----------
        query : dict of str to object
            Query fields.

        Returns
        -------
        ToolResult
            Product recovery with provenance.
        """
        try:
            parsed = parse_curve_query({**query, "format": "taf"})
        except ServiceError as exc:
            return _from_error("recover_products", {"query": query}, exc)
        return self._call(
            "recover_products",
            {"query": query},
            lambda: service_recover_products(self.catalog, self.source_root, parsed),
        )

    def run_economics(self, scenario: dict[str, object]) -> ToolResult:
        """Run an explicit economics scenario.

        Parameters
        ----------
        scenario : dict of str to object
            Scenario fields.

        Returns
        -------
        ToolResult
            Economics result with provenance and gaps.
        """
        try:
            parsed = parse_scenario(scenario)
        except ServiceError as exc:
            return _from_error("run_economics", {"scenario": scenario}, exc)
        return self._call(
            "run_economics",
            {"scenario": scenario},
            lambda: service_run_economics(self.catalog, self.source_root, parsed),
        )

    def get_provenance(self, asset_id: str) -> ToolResult:
        """Return one asset's provenance.

        Parameters
        ----------
        asset_id : str
            Stable asset ID.

        Returns
        -------
        ToolResult
            Asset provenance.
        """
        request: dict[str, object] = {"asset_id": asset_id}
        return self._call(
            "get_provenance",
            request,
            lambda: asset_provenance(self.catalog, asset_id),
        )


def tool_specs() -> tuple[dict[str, object], ...]:
    """Return bounded tool descriptions for an optional LLM adapter.

    Returns
    -------
    tuple of dict
        Tool names, descriptions, and input summaries.
    """
    return (
        {
            "name": "search_catalog",
            "description": "Search source tables and return metadata and checksums.",
        },
        {
            "name": "describe_table",
            "description": "Describe one table by stable asset ID.",
        },
        {
            "name": "query_curve",
            "description": "Query a growth curve with provenance.",
        },
        {
            "name": "compare_curves",
            "description": "Compare multiple growth queries.",
        },
        {
            "name": "recover_products",
            "description": "Recover product groups and mass-balance checks from a .taf table.",
        },
        {
            "name": "run_economics",
            "description": "Run an explicit price/cost/discount scenario.",
        },
        {
            "name": "get_provenance",
            "description": "Return the source provenance for one asset.",
        },
    )


# Local aliases keep the tool methods readable without shadowing their names.
service_query_curve = query_curve
service_recover_products = recover_products
service_run_economics = run_economics

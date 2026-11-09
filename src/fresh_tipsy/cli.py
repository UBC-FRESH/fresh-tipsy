"""Command-line interface for fresh-tipsy."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Annotated

import typer

from fresh_tipsy.curves import CurveEngine, CurveQuery
from fresh_tipsy.economics import (
    CostCategory,
    CostEntry,
    DiscountAssumptions,
    EconomicsRequest,
    PriceBook,
    PriceEntry,
    PriceKey,
    evaluate_economics,
)
from fresh_tipsy.products import ProductGroup
from fresh_tipsy.tables import (
    CatalogQuery,
    TableCatalog,
    TableFormatError,
    build_normalized_manifest_entries,
    build_tab_manifest_entry,
    build_taf_manifest_entry,
    normalize_table,
    parse_pair,
    write_normalized_assets,
)
from fresh_tipsy.tables.manifest_io import (
    ManifestError,
    build_manifest,
    load_manifest,
    validate_manifest_data,
    validate_manifest_files,
    write_manifest,
)

app = typer.Typer(
    no_args_is_help=True,
    help="Read and query BC TIPSY and FAN$IER data tables.",
)
db_app = typer.Typer(
    no_args_is_help=True,
    help="Extract, validate, and browse TIPSY database tables.",
)
curve_app = typer.Typer(
    no_args_is_help=True,
    help="Query growth curves from a validated catalog.",
)
product_app = typer.Typer(
    no_args_is_help=True,
    help="Recover product and grade values from a .taf table.",
)
econ_app = typer.Typer(
    no_args_is_help=True,
    help="Run explicit product economics and sensitivity.",
)
app.add_typer(db_app, name="db")
app.add_typer(curve_app, name="curve")
app.add_typer(product_app, name="product")
app.add_typer(econ_app, name="econ")


class CliError(ValueError):
    """Raised for a user-facing command error."""


def _fail(message: str) -> typer.Exit:
    """Print an error and return a failing exit.

    Parameters
    ----------
    message : str
        Error message.

    Returns
    -------
    typer.Exit
        Exit with code 1.
    """
    typer.echo(f"Error: {message}", err=True)
    return typer.Exit(code=1)


def _print_json(data: dict[str, object]) -> None:
    """Print a deterministic JSON object.

    Parameters
    ----------
    data : dict of str to object
        Data to print.
    """
    typer.echo(json.dumps(data, indent=2, sort_keys=True))


def _extract(source: Path, out: Path) -> dict[str, object]:
    """Extract all pairs under a source directory.

    Parameters
    ----------
    source : Path
        Database directory.
    out : Path
        Output directory.

    Returns
    -------
    dict of str to object
        Extraction summary.

    Raises
    ------
    CliError
        When the source is invalid or the manifest cannot be validated.
    TableFormatError
        When a table is malformed.
    NormalizationError
        When a table cannot be normalized.
    ManifestError
        When the manifest cannot be built.
    OSError
        When a file cannot be read or written.
    """
    if not source.is_dir():
        message = f"source directory does not exist: {source}"
        raise CliError(message)
    tabs = sorted(source.glob("*.tab"))
    if not tabs:
        message = f"no .tab files found in {source}"
        raise CliError(message)
    out.mkdir(parents=True, exist_ok=True)
    assets: list[dict[str, object]] = []
    gaps: list[dict[str, object]] = []
    age_mismatch_pairs = 0
    database_title = ""
    for tab_path in tabs:
        pair = parse_pair(tab_path)
        if pair.warnings:
            message = f"{tab_path.name}: " + "; ".join(pair.warnings)
            raise CliError(message)
        if not database_title:
            database_title = pair.tab.header.database_title
        if pair.age_mismatches or pair.age_range_mismatch:
            age_mismatch_pairs += 1
        assets.append(build_tab_manifest_entry(pair.tab, source))
        assets.append(build_taf_manifest_entry(pair.taf, source))
        for table in (pair.tab, pair.taf):
            normalized = normalize_table(table)
            table_dir = out / "tables" / "tipsy" / table.pair_id / table.format
            written = write_normalized_assets(normalized, table_dir)
            assets.extend(build_normalized_manifest_entries(normalized, written, out, source))
    if age_mismatch_pairs:
        gaps.append(
            {
                "id": "taf-tab-age-grid-mismatch",
                "kind": "schema_gap",
                "status": "planned",
                "reason": (f"{age_mismatch_pairs} pair(s) have different .tab and .taf age grids."),
                "required_for": ["P3 curve queries"],
                "notes": "Each table keeps its own age grid; no row alignment is assumed.",
            }
        )
    manifest = build_manifest(
        assets,
        {
            "model": "TIPSY",
            "version": "4.5",
            "database_title": database_title,
            "install_env": "TIPSY_INSTALL",
            "database_env": "TIPSY_DATABASE",
            "notes": "Source files are not redistributed.",
        },
        "fresh-tipsy db extract",
        gaps,
    )
    errors = validate_manifest_data(manifest)
    if errors:
        message = "manifest validation failed: " + "; ".join(errors[:5])
        raise CliError(message)
    manifest_path = write_manifest(manifest, out / "manifest.json")
    return {
        "status": "ok",
        "source": str(source),
        "output": str(out),
        "manifest": str(manifest_path),
        "tables": len(tabs),
        "assets": len(assets),
        "normalized_assets": len(assets) - (2 * len(tabs)),
        "age_mismatch_pairs": age_mismatch_pairs,
        "gaps": gaps,
    }


def _validate(catalog: Path, source: Path | None) -> tuple[dict[str, object], bool]:
    """Validate a manifest and its referenced files.

    Parameters
    ----------
    catalog : Path
        Manifest path.
    source : Path or None
        Optional source root for raw-file checks.

    Returns
    -------
    tuple of (dict of str to object, bool)
        Summary and success flag.

    Raises
    ------
    ManifestError
        When the manifest cannot be read.
    OSError
        When a file cannot be read.
    """
    if not catalog.is_file():
        message = f"manifest does not exist: {catalog}"
        raise ManifestError(message)
    manifest = load_manifest(catalog)
    schema_errors = validate_manifest_data(manifest)
    file_errors, warnings = validate_manifest_files(manifest, catalog.parent, source)
    errors = [*schema_errors, *file_errors]
    assets = manifest.get("assets")
    asset_list = assets if isinstance(assets, list) else []
    tables = [
        asset
        for asset in asset_list
        if isinstance(asset, dict) and asset.get("kind") == "tipsy_table"
    ]
    summary: dict[str, object] = {
        "status": "ok" if not errors else "error",
        "manifest": str(catalog),
        "assets": len(asset_list),
        "tables": len(tables),
        "errors": errors,
        "warnings": warnings,
    }
    return summary, not errors


@db_app.command("extract")
def extract(
    source: Annotated[Path, typer.Option("--source", help="TIPSY Database directory.")],
    out: Annotated[Path, typer.Option("--out", help="Output directory for assets and manifest.")],
    json_output: Annotated[bool, typer.Option("--json", help="Print a JSON summary.")] = False,
) -> None:
    """Extract every .tab/.taf pair, write normalized assets, and build a manifest."""
    try:
        summary = _extract(source, out)
    except (
        CliError,
        ManifestError,
        TableFormatError,
        ValueError,
        OSError,
    ) as exc:
        raise _fail(str(exc)) from exc
    if json_output:
        _print_json(summary)
    else:
        typer.echo(f"Extracted {summary['tables']} table pairs to {summary['output']}")
        typer.echo(f"Manifest: {summary['manifest']}")
        typer.echo(f"Assets: {summary['assets']}")


@db_app.command("validate")
def validate(
    catalog: Annotated[Path, typer.Option("--catalog", help="Manifest JSON path.")],
    source: Annotated[
        Path | None,
        typer.Option(
            "--source",
            help="Optional TIPSY Database directory for raw-file checks.",
        ),
    ] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Print a JSON summary.")] = False,
) -> None:
    """Validate a manifest against the schema and its referenced files."""
    try:
        summary, ok = _validate(catalog, source)
    except (ManifestError, ValueError, OSError) as exc:
        raise _fail(str(exc)) from exc
    if json_output:
        _print_json(summary)
    else:
        typer.echo(f"Manifest: {summary['manifest']}")
        typer.echo(f"Assets: {summary['assets']}; tables: {summary['tables']}")
        for warning in summary["warnings"] if isinstance(summary["warnings"], list) else []:
            typer.echo(f"Warning: {warning}", err=True)
        for error in summary["errors"] if isinstance(summary["errors"], list) else []:
            typer.echo(f"Error: {error}", err=True)
        if ok:
            typer.echo("Manifest valid.")
    if not ok:
        raise typer.Exit(code=1)


@db_app.command("catalog")
def catalog(
    catalog: Annotated[Path, typer.Option("--catalog", help="Manifest JSON path.")],
    species: Annotated[str | None, typer.Option("--species", help="Species code filter.")] = None,
    site_index: Annotated[
        float | None, typer.Option("--site-index", help="Site index filter.")
    ] = None,
    pnc: Annotated[str | None, typer.Option("--pnc", help="PNC filter: C, N, or P.")] = None,
    stock_height: Annotated[
        float | None, typer.Option("--stock-height", help="Stock height in metres.")
    ] = None,
    source_version: Annotated[
        str | None,
        typer.Option("--source-version", help="Source model version filter."),
    ] = None,
    table_format: Annotated[
        str | None, typer.Option("--format", help="Table format filter: tab or taf.")
    ] = None,
    query_text: Annotated[str | None, typer.Option("--query", help="Text search.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Print a JSON summary.")] = False,
) -> None:
    """Browse the table catalog with optional filters."""
    try:
        if not catalog.is_file():
            message = f"manifest does not exist: {catalog}"
            raise ManifestError(message)
        table_catalog = TableCatalog.from_manifest(catalog)
    except (ManifestError, ValueError, OSError) as exc:
        raise _fail(str(exc)) from exc
    query = CatalogQuery(
        species_code=species,
        site_index=site_index,
        pnc=pnc,
        stock_height_m=stock_height,
        source_version=source_version,
        format=table_format,
        text=query_text,
    )
    results = table_catalog.search(query)
    summary: dict[str, object] = {
        "status": "ok",
        "catalog": str(catalog),
        "count": len(results),
        "query": {
            "species": species,
            "site_index": site_index,
            "pnc": pnc,
            "stock_height": stock_height,
            "source_version": source_version,
            "format": table_format,
            "text": query_text,
        },
        "tables": [entry.as_dict() for entry in results],
    }
    if json_output:
        _print_json(summary)
        return
    if not results:
        typer.echo("No tables matched.")
        return
    for entry in results:
        typer.echo(
            f"{entry.asset_id}  {entry.species_code} {entry.species_name}  "
            f"site {entry.site_from}-{entry.site_to}  PNC {entry.pnc}  "
            f"{entry.data_rows} rows  {entry.format}"
        )


def _source_root(source: Path | None) -> Path:
    """Resolve a source root for catalog queries.

    Parameters
    ----------
    source : Path or None
        Explicit install root, or ``None`` to use ``TIPSY_INSTALL``.

    Returns
    -------
    Path
        Source root.

    Raises
    ------
    CliError
        When no source root is available.
    """
    if source is not None:
        return source
    configured = os.environ.get("TIPSY_INSTALL")
    if configured:
        return Path(configured)
    message = "--source is required unless TIPSY_INSTALL is set"
    raise CliError(message)


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
    ManifestError
        When the manifest is missing or invalid.
    CliError
        When no source root is available.
    """
    if not catalog.is_file():
        message = f"manifest does not exist: {catalog}"
        raise ManifestError(message)
    return CurveEngine.from_manifest(catalog, source_root=_source_root(source))


def _query_payload(query: CurveQuery) -> dict[str, object]:
    """Return the query portion of a machine-readable response.

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


def _optional_float(data: dict[str, object], key: str) -> float | None:
    """Read an optional numeric scenario field.

    Parameters
    ----------
    data : dict of str to object
        Scenario object.
    key : str
        Field name.

    Returns
    -------
    float or None
        Parsed value.
    """
    value = data.get(key)
    return None if value is None else float(str(value))


def _optional_int(data: dict[str, object], key: str) -> int | None:
    """Read an optional integer scenario field.

    Parameters
    ----------
    data : dict of str to object
        Scenario object.
    key : str
        Field name.

    Returns
    -------
    int or None
        Parsed value.
    """
    value = data.get(key)
    return None if value is None else int(float(str(value)))


def _scenario_query(data: dict[str, object]) -> CurveQuery:
    """Build a curve query from a scenario object.

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
    CliError
        When the scenario query is malformed.
    """
    raw = data.get("query")
    if not isinstance(raw, dict):
        message = "scenario.query must be an object"
        raise CliError(message)
    try:
        return CurveQuery(
            species_code=str(raw["species_code"]),
            site_index=float(raw["site_index"]),
            age=float(raw["age"]),
            pnc=None if raw.get("pnc") is None else str(raw["pnc"]),
            stock_height_m=_optional_float(raw, "stock_height_m"),
            source_version=(
                None if raw.get("source_version") is None else str(raw["source_version"])
            ),
            scenario=None if raw.get("scenario") is None else str(raw["scenario"]),
            initial_density=_optional_int(raw, "initial_density"),
            pct_density=_optional_int(raw, "pct_density"),
            ct_density=_optional_int(raw, "ct_density"),
            format=str(raw.get("format", "taf")),
        )
    except (KeyError, TypeError, ValueError) as exc:
        message = f"invalid scenario.query: {exc}"
        raise CliError(message) from exc


def _scenario_request(
    data: dict[str, object], catalog: Path, source: Path | None
) -> EconomicsRequest:
    """Build an economics request from a scenario object.

    Parameters
    ----------
    data : dict of str to object
        Scenario object.
    catalog : Path
        Manifest path.
    source : Path or None
        Source install root.

    Returns
    -------
    EconomicsRequest
        Typed economics request.

    Raises
    ------
    CliError
        When the scenario is malformed.
    """
    query = _scenario_query(data)
    engine = _engine(catalog, source)
    recovery = engine.products(query)
    period = str(data.get("period", "default"))
    raw_groups = data.get("revenue_groups")
    if not isinstance(raw_groups, list) or not raw_groups:
        message = "scenario.revenue_groups must be a non-empty list"
        raise CliError(message)
    try:
        groups = tuple(ProductGroup(str(group)) for group in raw_groups)
    except ValueError as exc:
        message = f"invalid scenario.revenue_groups: {exc}"
        raise CliError(message) from exc
    raw_prices = data.get("prices", [])
    if not isinstance(raw_prices, list):
        message = "scenario.prices must be a list"
        raise CliError(message)
    prices: list[PriceEntry] = []
    for index, raw_price in enumerate(raw_prices):
        if not isinstance(raw_price, dict):
            message = f"scenario.prices[{index}] must be an object"
            raise CliError(message)
        key_data = raw_price.get("key", raw_price)
        if not isinstance(key_data, dict):
            message = f"scenario.prices[{index}].key must be an object"
            raise CliError(message)
        try:
            key = PriceKey(
                species_code=str(key_data.get("species_code", query.species_code)),
                group=ProductGroup(str(key_data["group"])),
                period=str(key_data.get("period", period)),
                grade=None if key_data.get("grade") is None else str(key_data["grade"]),
                dimension=(
                    None if key_data.get("dimension") is None else str(key_data["dimension"])
                ),
                detail=None if key_data.get("detail") is None else str(key_data["detail"]),
            )
            prices.append(
                PriceEntry(
                    key=key,
                    price_per_unit=float(raw_price["price_per_unit"]),
                    unit=str(raw_price["unit"]),
                    source=str(raw_price.get("source", "scenario")),
                    citation=str(raw_price.get("citation", "Scenario input.")),
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            message = f"invalid scenario.prices[{index}]: {exc}"
            raise CliError(message) from exc
    raw_costs = data.get("costs", [])
    if not isinstance(raw_costs, list):
        message = "scenario.costs must be a list"
        raise CliError(message)
    costs: list[CostEntry] = []
    for index, raw_cost in enumerate(raw_costs):
        if not isinstance(raw_cost, dict):
            message = f"scenario.costs[{index}] must be an object"
            raise CliError(message)
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
            message = f"invalid scenario.costs[{index}]: {exc}"
            raise CliError(message) from exc
    raw_assumptions = data.get("assumptions")
    if not isinstance(raw_assumptions, dict):
        message = "scenario.assumptions must be an object"
        raise CliError(message)
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
        message = f"invalid scenario.assumptions: {exc}"
        raise CliError(message) from exc
    try:
        return EconomicsRequest(
            recovery=recovery,
            price_book=PriceBook(tuple(prices)),
            assumptions=assumptions,
            revenue_groups=groups,
            costs=tuple(costs),
            period=period,
        )
    except ValueError as exc:
        message = f"invalid scenario: {exc}"
        raise CliError(message) from exc


@curve_app.command("query")
def curve_query(
    catalog: Annotated[Path, typer.Option("--catalog", help="Manifest JSON path.")],
    species: Annotated[str, typer.Option("--species", help="Species code.")],
    site_index: Annotated[float, typer.Option("--site-index", help="Site index.")],
    age: Annotated[float, typer.Option("--age", help="Query age in years.")],
    source: Annotated[Path | None, typer.Option("--source", help="TIPSY install root.")] = None,
    pnc: Annotated[str | None, typer.Option("--pnc", help="PNC filter.")] = None,
    stock_height: Annotated[
        float | None, typer.Option("--stock-height", help="Stock height in metres.")
    ] = None,
    source_version: Annotated[
        str | None, typer.Option("--source-version", help="Source version filter.")
    ] = None,
    scenario: Annotated[
        str | None, typer.Option("--scenario", help="Treatment scenario filter.")
    ] = None,
    table_format: Annotated[
        str, typer.Option("--format", help="Source format: tab or taf.")
    ] = "tab",
    initial_density: Annotated[
        int | None, typer.Option("--initial-density", help="Initial density filter.")
    ] = None,
    pct_density: Annotated[
        int | None, typer.Option("--pct-density", help="Post-PCT density filter.")
    ] = None,
    ct_density: Annotated[
        int | None, typer.Option("--ct-density", help="Post-CT density filter.")
    ] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Print JSON.")] = False,
) -> None:
    """Query a growth curve and print typed metrics with provenance."""
    try:
        engine = _engine(catalog, source)
        query = CurveQuery(
            species_code=species,
            site_index=site_index,
            age=age,
            pnc=pnc,
            stock_height_m=stock_height,
            source_version=source_version,
            scenario=scenario,
            initial_density=initial_density,
            pct_density=pct_density,
            ct_density=ct_density,
            format=table_format,
        )
        point = engine.point(query)
    except (CliError, ManifestError, ValueError, OSError) as exc:
        raise _fail(str(exc)) from exc
    payload: dict[str, object] = {
        "status": "ok",
        "query": _query_payload(query),
        "result": point.as_dict(),
        "evidence": point.provenance.evidence,
        "warnings": [],
    }
    if json_output:
        _print_json(payload)
        return
    typer.echo(f"{point.age:g} yr  {point.format}  {point.provenance.relative_path}")
    typer.echo(
        f"Volume gross {point.volume_gross_m3_ha}, height site {point.height_site_m}, "
        f"stems {point.stems_per_ha}"
    )
    if point.unavailable_metrics:
        typer.echo("Unavailable: " + ", ".join(point.unavailable_metrics), err=True)


@product_app.command("recover")
def product_recover(
    catalog: Annotated[Path, typer.Option("--catalog", help="Manifest JSON path.")],
    species: Annotated[str, typer.Option("--species", help="Species code.")],
    site_index: Annotated[float, typer.Option("--site-index", help="Site index.")],
    age: Annotated[float, typer.Option("--age", help="Query age in years.")],
    source: Annotated[Path | None, typer.Option("--source", help="TIPSY install root.")] = None,
    pnc: Annotated[str | None, typer.Option("--pnc", help="PNC filter.")] = None,
    stock_height: Annotated[
        float | None, typer.Option("--stock-height", help="Stock height in metres.")
    ] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Print JSON.")] = False,
) -> None:
    """Recover product groups and run mass-balance checks."""
    try:
        engine = _engine(catalog, source)
        query = CurveQuery(
            species_code=species,
            site_index=site_index,
            age=age,
            pnc=pnc,
            stock_height_m=stock_height,
            format="taf",
        )
        recovery = engine.products(query)
    except (CliError, ManifestError, ValueError, OSError) as exc:
        raise _fail(str(exc)) from exc
    payload: dict[str, object] = {
        "status": "ok",
        "query": _query_payload(query),
        "result": recovery.as_dict(),
        "evidence": "model_output",
        "warnings": [],
    }
    if json_output:
        _print_json(payload)
        return
    typer.echo(f"Product recovery at {recovery.age:g} yr ({recovery.species_code})")
    typer.echo(f"#2 & Better: {recovery.totals.lumber_2_or_better_bf_ha} bf/ha")
    typer.echo(f"Graded: {recovery.totals.graded_bf_ha} bf/ha")
    typer.echo(f"Logs: {recovery.totals.logs_m3_ha} m3/ha")
    typer.echo(f"Residues: {recovery.totals.residues_odt_ha} ODT/ha")
    for check in recovery.checks:
        if check.status != "pass":
            typer.echo(f"{check.name}: {check.status}", err=True)


@econ_app.command("run")
def econ_run(
    catalog: Annotated[Path, typer.Option("--catalog", help="Manifest JSON path.")],
    scenario: Annotated[Path, typer.Option("--scenario", help="Scenario JSON path.")],
    source: Annotated[Path | None, typer.Option("--source", help="TIPSY install root.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Print JSON.")] = False,
) -> None:
    """Run an explicit price/cost/NPV scenario."""
    try:
        if not scenario.is_file():
            message = f"scenario does not exist: {scenario}"
            raise CliError(message)
        data = json.loads(scenario.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            message = "scenario must be a JSON object"
            raise CliError(message)
        request = _scenario_request(data, catalog, source)
        result = evaluate_economics(request)
    except (CliError, ManifestError, ValueError, OSError) as exc:
        raise _fail(str(exc)) from exc
    payload: dict[str, object] = {
        "status": "ok",
        "query": _query_payload(_scenario_query(data)),
        "result": result.as_dict(),
        "evidence": result.evidence,
        "warnings": [gap.as_dict() for gap in result.gaps],
    }
    if json_output:
        _print_json(payload)
        return
    typer.echo(f"Revenue: {result.revenue_per_ha} CAD/ha")
    typer.echo(f"Cost: {result.cost_per_ha} CAD/ha")
    typer.echo(f"NPV: {result.npv_per_ha} CAD/ha")
    typer.echo(f"Site value: {result.site_value_per_ha} CAD/ha")
    for gap in result.gaps:
        typer.echo(f"{gap.code}: {gap.message}", err=True)


def main() -> None:
    """Run the fresh-tipsy CLI."""
    app()

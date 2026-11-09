"""Command-line interface for fresh-tipsy."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from fresh_tipsy.api.service import (
    ServiceError,
    parse_scenario,
    query_curve,
    recover_products,
    run_economics,
)
from fresh_tipsy.curves import CurveQuery
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
        response = query_curve(catalog, source, query)
    except (ServiceError, ValueError, OSError) as exc:
        raise _fail(str(exc)) from exc
    if json_output:
        _print_json(response.as_dict())
        return
    result = response.result or {}
    typer.echo(
        f"{result.get('age')} yr  {result.get('format')}  "
        f"{response.provenance['relative_path'] if response.provenance else ''}"
    )
    typer.echo(
        f"Volume gross {result.get('volume_gross_m3_ha')}, "
        f"height site {result.get('height_site_m')}, "
        f"stems {result.get('stems_per_ha')}"
    )
    for warning in response.warnings:
        typer.echo(f"{warning.code}: {warning.message}", err=True)


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
        query = CurveQuery(
            species_code=species,
            site_index=site_index,
            age=age,
            pnc=pnc,
            stock_height_m=stock_height,
            format="taf",
        )
        response = recover_products(catalog, source, query)
    except (ServiceError, ValueError, OSError) as exc:
        raise _fail(str(exc)) from exc
    if json_output:
        _print_json(response.as_dict())
        return
    result = response.result or {}
    totals = result.get("totals")
    typer.echo(f"Product recovery at {result.get('age')} yr ({result.get('species_code')})")
    if isinstance(totals, dict):
        typer.echo(f"#2 & Better: {totals.get('lumber_2_or_better_bf_ha')} bf/ha")
        typer.echo(f"Graded: {totals.get('graded_bf_ha')} bf/ha")
        typer.echo(f"Logs: {totals.get('logs_m3_ha')} m3/ha")
        typer.echo(f"Residues: {totals.get('residues_odt_ha')} ODT/ha")
    for warning in response.warnings:
        typer.echo(f"{warning.code}: {warning.message}", err=True)


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
        response = run_economics(catalog, source, parse_scenario(data))
    except (ServiceError, ValueError, OSError) as exc:
        raise _fail(str(exc)) from exc
    if json_output:
        _print_json(response.as_dict())
        return
    result = response.result or {}
    typer.echo(f"Revenue: {result.get('revenue_per_ha')} CAD/ha")
    typer.echo(f"Cost: {result.get('cost_per_ha')} CAD/ha")
    typer.echo(f"NPV: {result.get('npv_per_ha')} CAD/ha")
    typer.echo(f"Site value: {result.get('site_value_per_ha')} CAD/ha")
    for warning in response.warnings:
        typer.echo(f"{warning.code}: {warning.message}", err=True)


def main() -> None:
    """Run the fresh-tipsy CLI."""
    app()

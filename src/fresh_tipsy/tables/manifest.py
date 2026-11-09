"""Manifest entries for parsed TIPSY assets."""

from __future__ import annotations

from pathlib import Path

from fresh_tipsy.tables.formats import TAB_COLUMNS, TAF_COLUMNS_REF, TAF_FIELD_COUNT
from fresh_tipsy.tables.parsers import TIPSYTable


def build_tab_manifest_entry(
    table: TIPSYTable,
    source_root: Path,
    model_version: str = "4.5",
) -> dict[str, object]:
    """Build a P1.4 manifest entry for one compact ``.tab`` asset.

    Parameters
    ----------
    table : TIPSYTable
        Parsed table.
    source_root : Path
        Installation root that contains the table.
    model_version : str, optional
        TIPSY version.

    Returns
    -------
    dict of str to object
        One manifest asset entry, ready for the manifest envelope.

    Raises
    ------
    ValueError
        When the table path is not under the source root or the table is not
        a ``.tab`` table.
    """
    if table.format != "tab":
        message = f"expected a .tab table, got {table.format!r}"
        raise ValueError(message)
    try:
        relative_path = table.path.resolve().relative_to(source_root.resolve()).as_posix()
    except ValueError as exc:
        message = f"table path {table.path} is not under source root {source_root}"
        raise ValueError(message) from exc
    columns: list[dict[str, object]] = [
        {
            "position": spec.position,
            "name": spec.name,
            "units": spec.units,
            "evidence": spec.evidence,
            "confidence": spec.confidence,
        }
        for spec in TAB_COLUMNS
    ]
    table_entry: dict[str, object] = {
        "pair_id": table.pair_id,
        "format": "tab",
        "field_count": table.field_count,
        "data_rows": table.data_rows,
        "run_count": table.run_count,
        "field_count_rule": "Every non-empty data row has 22 fields.",
        "treatments": list(table.treatments),
    }
    if table.first_age is not None:
        table_entry["first_age"] = table.first_age
    if table.last_age is not None:
        table_entry["last_age"] = table.last_age
    validation: dict[str, object] = {
        "status": "warn" if table.warnings else "pass",
        "checks": [
            "sha256 and size recorded from the source bytes",
            "field_count is 22 for every data row",
            "run blocks parsed in source order",
            "filename and header metadata compared",
        ],
    }
    if table.warnings:
        validation["warnings"] = list(table.warnings)
    return {
        "id": table.asset_id,
        "kind": "tipsy_table",
        "format": "tab",
        "role": "source_table",
        "evidence": "source_table",
        "publication": "manifest_only",
        "source": {
            "model": "TIPSY",
            "version": model_version,
            "build": table.header.source,
            "database_title": table.header.database_title,
            "relative_path": relative_path,
            "sha256": table.sha256,
            "size_bytes": table.size_bytes,
        },
        "table": table_entry,
        "columns": columns,
        "citation": f"Province of British Columbia. TIPSY {model_version}. {relative_path}.",
        "validation": validation,
        "notes": "Compact TIPSY yield table; product and grade columns are not present.",
    }


def build_taf_manifest_entry(
    table: TIPSYTable,
    source_root: Path,
    model_version: str = "4.5",
) -> dict[str, object]:
    """Build a P1.4 manifest entry for one full ``.taf`` asset.

    Parameters
    ----------
    table : TIPSYTable
        Parsed table.
    source_root : Path
        Installation root that contains the table.
    model_version : str, optional
        TIPSY version.

    Returns
    -------
    dict of str to object
        One manifest asset entry, ready for the manifest envelope.

    Raises
    ------
    ValueError
        When the table path is not under the source root or the table is not
        a ``.taf`` table.
    """
    if table.format != "taf":
        message = f"expected a .taf table, got {table.format!r}"
        raise ValueError(message)
    try:
        relative_path = table.path.resolve().relative_to(source_root.resolve()).as_posix()
    except ValueError as exc:
        message = f"table path {table.path} is not under source root {source_root}"
        raise ValueError(message) from exc
    table_entry: dict[str, object] = {
        "pair_id": table.pair_id,
        "format": "taf",
        "field_count": table.field_count,
        "data_rows": table.data_rows,
        "run_count": table.run_count,
        "field_count_rule": "Every non-empty data row has 151 fields.",
        "treatments": list(table.treatments),
    }
    if table.first_age is not None:
        table_entry["first_age"] = table.first_age
    if table.last_age is not None:
        table_entry["last_age"] = table.last_age
    validation: dict[str, object] = {
        "status": "warn" if table.warnings else "pass",
        "checks": [
            "sha256 and size recorded from the source bytes",
            "field_count is 151 for every data row",
            "run blocks parsed in source order",
            "filename and header metadata compared",
        ],
    }
    if table.warnings:
        validation["warnings"] = list(table.warnings)
    return {
        "id": table.asset_id,
        "kind": "tipsy_table",
        "format": "taf",
        "role": "source_table",
        "evidence": "model_output",
        "publication": "manifest_only",
        "source": {
            "model": "TIPSY",
            "version": model_version,
            "build": table.header.source,
            "database_title": table.header.database_title,
            "relative_path": relative_path,
            "sha256": table.sha256,
            "size_bytes": table.size_bytes,
        },
        "table": table_entry,
        "columns_ref": TAF_COLUMNS_REF,
        "column_count": TAF_FIELD_COUNT,
        "citation": f"Province of British Columbia. TIPSY {model_version}. {relative_path}.",
        "validation": validation,
        "notes": (
            "Full TIPSY table. Product and grade columns are TASS/SYLVER model "
            "output, not measured field grades."
        ),
    }

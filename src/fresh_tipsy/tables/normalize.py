"""Normalized CSV and Parquet assets for TIPSY tables."""

from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final

from fresh_tipsy.tables.columns import load_columns
from fresh_tipsy.tables.formats import (
    TAB_COLUMNS_REF,
    TAF_COLUMNS_REF,
    ColumnSpec,
)
from fresh_tipsy.tables.manifest import build_table_metadata
from fresh_tipsy.tables.metadata import slugify
from fresh_tipsy.tables.parsers import TIPSYTable

if TYPE_CHECKING:
    import pyarrow as pa

_FORMATS: Final[frozenset[str]] = frozenset({"csv", "parquet"})


class NormalizationError(ValueError):
    """Raised when a table cannot be normalized or round-tripped."""


@dataclass(frozen=True)
class NormalizedRow:
    """One normalized row.

    Parameters
    ----------
    age : float or None
        Parsed age.
    values : tuple of float or None
        Parsed non-age values.
    raw : tuple of str
        Original raw fields, including the age field.
    """

    age: float | None
    values: tuple[float | None, ...]
    raw: tuple[str, ...]


@dataclass(frozen=True)
class NormalizedTable:
    """A normalized TIPSY table.

    Parameters
    ----------
    source : TIPSYTable
        Parsed source table.
    columns : tuple of ColumnSpec
        Column specifications.
    rows : tuple of NormalizedRow
        Rows in source order.
    """

    source: TIPSYTable
    columns: tuple[ColumnSpec, ...]
    rows: tuple[NormalizedRow, ...]

    @property
    def data_rows(self) -> int:
        """Return the normalized row count."""
        return len(self.rows)


@dataclass(frozen=True)
class NormalizedAssets:
    """Paths and checksums for the written normalized assets.

    Parameters
    ----------
    csv_path : Path
        Written CSV path.
    parquet_path : Path
        Written Parquet path.
    csv_sha256 : str
        CSV SHA-256.
    parquet_sha256 : str
        Parquet SHA-256.
    csv_size_bytes : int
        CSV size.
    parquet_size_bytes : int
        Parquet size.
    """

    csv_path: Path
    parquet_path: Path
    csv_sha256: str
    parquet_sha256: str
    csv_size_bytes: int
    parquet_size_bytes: int


def _parse_field(raw: str, position: int) -> float | None:
    """Parse one numeric field while preserving blanks.

    Parameters
    ----------
    raw : str
        Raw field.
    position : int
        Zero-based field position for errors.

    Returns
    -------
    float or None
        Parsed value, or ``None`` when blank.

    Raises
    ------
    NormalizationError
        When the field is not numeric.
    """
    text = raw.strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError as exc:
        message = f"field {position} is not numeric: {raw!r}"
        raise NormalizationError(message) from exc


def normalize_table(table: TIPSYTable) -> NormalizedTable:
    """Normalize a parsed table into typed rows.

    Parameters
    ----------
    table : TIPSYTable
        Parsed source table.

    Returns
    -------
    NormalizedTable
        Normalized rows in source order.

    Raises
    ------
    NormalizationError
        When a field is non-numeric or the column count disagrees.
    """
    columns = load_columns(table.format)
    if len(columns) != table.field_count:
        message = (
            f"{table.format} has {table.field_count} fields but "
            f"{len(columns)} column specifications"
        )
        raise NormalizationError(message)
    rows: list[NormalizedRow] = []
    for block in table.blocks:
        for row in block.rows:
            parsed = tuple(_parse_field(value, index) for index, value in enumerate(row.fields))
            rows.append(
                NormalizedRow(
                    age=parsed[0],
                    values=parsed[1:],
                    raw=row.fields,
                )
            )
    return NormalizedTable(source=table, columns=columns, rows=tuple(rows))


def write_csv(normalized: NormalizedTable, path: Path) -> Path:
    """Write a normalized CSV asset.

    Parameters
    ----------
    normalized : NormalizedTable
        Normalized table.
    path : Path
        Output path.

    Returns
    -------
    Path
        The written path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    header = tuple(column.name for column in normalized.columns)
    with path.open("w", encoding="ascii", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        for row in normalized.rows:
            writer.writerow(row.raw)
    return path


def write_parquet(normalized: NormalizedTable, path: Path) -> Path:
    """Write a normalized Parquet asset.

    Parameters
    ----------
    normalized : NormalizedTable
        Normalized table.
    path : Path
        Output path.

    Returns
    -------
    Path
        The written path.

    Raises
    ------
    NormalizationError
        When pyarrow is not installed.
    """
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as exc:
        message = "pyarrow is required for Parquet output; install the parquet extra"
        raise NormalizationError(message) from exc
    path.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, pa.Array] = {
        normalized.columns[0].name: pa.array(
            [row.age for row in normalized.rows], type=pa.float64()
        )
    }
    for index, column in enumerate(normalized.columns[1:]):
        data[column.name] = pa.array(
            [row.values[index] for row in normalized.rows], type=pa.float64()
        )
    pq.write_table(pa.table(data), path)
    return path


def _sha256(path: Path) -> str:
    """Return a file SHA-256.

    Parameters
    ----------
    path : Path
        File to hash.

    Returns
    -------
    str
        Lowercase SHA-256.
    """
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_normalized_assets(normalized: NormalizedTable, output_dir: Path) -> NormalizedAssets:
    """Write CSV and Parquet assets and record their checksums.

    Parameters
    ----------
    normalized : NormalizedTable
        Normalized table.
    output_dir : Path
        Directory for ``data.csv`` and ``data.parquet``.

    Returns
    -------
    NormalizedAssets
        Written paths, sizes, and checksums.
    """
    csv_path = write_csv(normalized, output_dir / "data.csv")
    parquet_path = write_parquet(normalized, output_dir / "data.parquet")
    return NormalizedAssets(
        csv_path=csv_path,
        parquet_path=parquet_path,
        csv_sha256=_sha256(csv_path),
        parquet_sha256=_sha256(parquet_path),
        csv_size_bytes=csv_path.stat().st_size,
        parquet_size_bytes=parquet_path.stat().st_size,
    )


def verify_round_trip(normalized: NormalizedTable, assets: NormalizedAssets) -> None:
    """Verify CSV and Parquet round trips against the normalized rows.

    Parameters
    ----------
    normalized : NormalizedTable
        Expected normalized table.
    assets : NormalizedAssets
        Written assets.

    Raises
    ------
    NormalizationError
        When a header, row count, or value differs.
    """
    with assets.csv_path.open(encoding="ascii", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        rows = [tuple(row) for row in reader]
    expected_header = tuple(column.name for column in normalized.columns)
    if tuple(header) != expected_header:
        message = "CSV header differs from the column map"
        raise NormalizationError(message)
    expected_rows = [row.raw for row in normalized.rows]
    if rows != expected_rows:
        message = "CSV rows differ from the source rows"
        raise NormalizationError(message)
    try:
        import pyarrow.parquet as pq
    except ImportError as exc:
        message = "pyarrow is required to verify Parquet output"
        raise NormalizationError(message) from exc
    arrow_table = pq.read_table(assets.parquet_path)
    if arrow_table.num_rows != len(normalized.rows):
        message = "Parquet row count differs from the source"
        raise NormalizationError(message)
    if tuple(arrow_table.column_names) != expected_header:
        message = "Parquet columns differ from the column map"
        raise NormalizationError(message)
    data = arrow_table.to_pydict()
    for row_index, row in enumerate(normalized.rows):
        if data[normalized.columns[0].name][row_index] != row.age:
            message = f"Parquet age differs at row {row_index}"
            raise NormalizationError(message)
        for index, column in enumerate(normalized.columns[1:]):
            if data[column.name][row_index] != row.values[index]:
                message = f"Parquet value differs at row {row_index}, column {column.name}"
                raise NormalizationError(message)


def build_normalized_manifest_entry(
    normalized: NormalizedTable,
    assets: NormalizedAssets,
    artifact_format: str,
    output_root: Path,
    source_root: Path,
    model_version: str = "4.5",
) -> dict[str, object]:
    """Build a manifest entry for one normalized asset.

    Parameters
    ----------
    normalized : NormalizedTable
        Normalized table.
    assets : NormalizedAssets
        Written assets.
    artifact_format : str
        ``"csv"`` or ``"parquet"``.
    output_root : Path
        Release output root.
    source_root : Path
        TIPSY installation root.
    model_version : str, optional
        TIPSY version.

    Returns
    -------
    dict of str to object
        One normalized manifest asset entry.

    Raises
    ------
    NormalizationError
        When the format is unsupported or a path is outside its root.
    """
    if artifact_format not in _FORMATS:
        message = f"unsupported normalized format: {artifact_format!r}"
        raise NormalizationError(message)
    source = normalized.source
    artifact_path = assets.csv_path if artifact_format == "csv" else assets.parquet_path
    artifact_sha = assets.csv_sha256 if artifact_format == "csv" else assets.parquet_sha256
    artifact_size = assets.csv_size_bytes if artifact_format == "csv" else assets.parquet_size_bytes
    try:
        relative_artifact = artifact_path.resolve().relative_to(output_root.resolve()).as_posix()
        relative_source = source.path.resolve().relative_to(source_root.resolve()).as_posix()
    except ValueError as exc:
        message = "normalized or source path is outside its declared root"
        raise NormalizationError(message) from exc
    table_entry: dict[str, object] = {
        "pair_id": source.pair_id,
        "format": source.format,
        "field_count": source.field_count,
        "data_rows": normalized.data_rows,
        "run_count": source.run_count,
        "field_count_rule": f"Every source data row has {source.field_count} fields.",
        "treatments": list(source.treatments),
    }
    if source.first_age is not None:
        table_entry["first_age"] = source.first_age
    if source.last_age is not None:
        table_entry["last_age"] = source.last_age
    columns_ref = TAF_COLUMNS_REF if source.format == "taf" else TAB_COLUMNS_REF
    return {
        "id": f"normalized-{slugify(source.path.stem)}-{artifact_format}",
        "kind": "normalized_table",
        "format": artifact_format,
        "role": "release_asset",
        "evidence": "model_output" if source.format == "taf" else "source_table",
        "publication": "release_asset",
        "source": {
            "model": "TIPSY",
            "version": model_version,
            "build": source.header.source,
            "database_title": source.header.database_title,
            "relative_path": relative_source,
            "sha256": source.sha256,
            "size_bytes": source.size_bytes,
        },
        "source_asset_ids": [source.asset_id],
        "artifact": {
            "relative_path": relative_artifact,
            "sha256": artifact_sha,
            "size_bytes": artifact_size,
        },
        "table": table_entry,
        "metadata": build_table_metadata(source),
        "columns_ref": columns_ref,
        "column_count": len(normalized.columns),
        "citation": f"Province of British Columbia. TIPSY {model_version}. {relative_source}.",
        "validation": {
            "status": "pass",
            "checks": [
                "artifact sha256 and size computed",
                "row count matches the source",
                "CSV and Parquet round trips verified",
                "source asset IDs recorded",
            ],
        },
        "notes": "Normalized release asset; the raw source is not committed.",
    }


def build_normalized_manifest_entries(
    normalized: NormalizedTable,
    assets: NormalizedAssets,
    output_root: Path,
    source_root: Path,
    model_version: str = "4.5",
) -> list[dict[str, object]]:
    """Build manifest entries for the CSV and Parquet assets.

    Parameters
    ----------
    normalized : NormalizedTable
        Normalized table.
    assets : NormalizedAssets
        Written assets.
    output_root : Path
        Release output root.
    source_root : Path
        TIPSY installation root.
    model_version : str, optional
        TIPSY version.

    Returns
    -------
    list of dict of str to object
        CSV and Parquet manifest entries.
    """
    return [
        build_normalized_manifest_entry(
            normalized,
            assets,
            artifact_format,
            output_root,
            source_root,
            model_version,
        )
        for artifact_format in ("csv", "parquet")
    ]

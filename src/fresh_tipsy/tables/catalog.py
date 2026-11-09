"""Table catalog and search index over a fresh-tipsy manifest."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from fresh_tipsy.tables.columns import load_columns
from fresh_tipsy.tables.formats import ColumnSpec

_PNC_VALUES: Final[frozenset[str]] = frozenset({"C", "N", "P"})


class CatalogError(ValueError):
    """Raised when a manifest cannot be loaded into the catalog."""


@dataclass(frozen=True)
class CatalogQuery:
    """A table catalog query.

    Parameters
    ----------
    species_code : str or None, optional
        Species code filter.
    site_index : float or None, optional
        Site index that must fall inside the table's site range.
    pnc : str or None, optional
        PNC filter.
    stock_height_m : float or None, optional
        Exact stock-height filter.
    source_version : str or None, optional
        Source model version filter.
    format : str or None, optional
        ``"tab"`` or ``"taf"``.
    text : str or None, optional
        Case-insensitive text search over names, paths, and citations.
    """

    species_code: str | None = None
    site_index: float | None = None
    pnc: str | None = None
    stock_height_m: float | None = None
    source_version: str | None = None
    format: str | None = None
    text: str | None = None


@dataclass(frozen=True)
class CatalogEntry:
    """One table in the catalog.

    Parameters
    ----------
    asset_id : str
        Stable manifest asset ID.
    pair_id : str or None
        Shared `.tab`/`.taf` pair ID.
    kind : str
        Manifest kind.
    format : str
        ``"tab"`` or ``"taf"``.
    evidence : str
        Evidence label.
    publication : str
        Publication boundary.
    source_model : str
        Source model name.
    source_version : str
        Source model version.
    source_build : str or None
        Source build string.
    database_title : str or None
        Database edition.
    relative_path : str
        Source path relative to the install root.
    sha256 : str
        Source SHA-256.
    size_bytes : int
        Source size.
    species_code : str
        Uppercase species code.
    species_name : str
        Species display name.
    site_from : int
        Minimum site index.
    site_to : int
        Maximum site index.
    pnc : str
        PNC code.
    stock_height_m : float or None
        Planting stock height.
    stock_age_years : float or None
        Planting stock age.
    pct_height_m : int or None
        PCT treatment height.
    ct_height_m : int or None
        CT treatment height.
    field_count : int
        Field count per data row.
    data_rows : int
        Number of data rows.
    run_count : int
        Number of run blocks.
    first_age : float or None
        Minimum age.
    last_age : float or None
        Maximum age.
    treatments : tuple of str
        Treatment labels.
    columns : tuple of ColumnSpec
        Column specifications.
    columns_ref : str or None
        Optional column-map reference.
    column_count : int
        Number of columns.
    citation : str
        Source citation.
    validation_status : str
        Manifest validation status.
    validation_warnings : tuple of str
        Manifest validation warnings.
    """

    asset_id: str
    pair_id: str | None
    kind: str
    format: str
    evidence: str
    publication: str
    source_model: str
    source_version: str
    source_build: str | None
    database_title: str | None
    relative_path: str
    sha256: str
    size_bytes: int
    species_code: str
    species_name: str
    site_from: int
    site_to: int
    pnc: str
    stock_height_m: float | None
    stock_age_years: float | None
    pct_height_m: int | None
    ct_height_m: int | None
    field_count: int
    data_rows: int
    run_count: int
    first_age: float | None
    last_age: float | None
    treatments: tuple[str, ...]
    columns: tuple[ColumnSpec, ...]
    columns_ref: str | None
    column_count: int
    citation: str
    validation_status: str
    validation_warnings: tuple[str, ...]

    def matches(self, query: CatalogQuery) -> bool:
        """Report whether the entry matches a query.

        Parameters
        ----------
        query : CatalogQuery
            Query filters.

        Returns
        -------
        bool
            ``True`` when every supplied filter matches.
        """
        if query.species_code is not None and self.species_code != query.species_code.upper():
            return False
        if query.site_index is not None and not (
            self.site_from <= query.site_index <= self.site_to
        ):
            return False
        if query.pnc is not None and self.pnc != query.pnc.upper():
            return False
        if query.stock_height_m is not None:
            if self.stock_height_m is None:
                return False
            if abs(self.stock_height_m - query.stock_height_m) > 1e-9:
                return False
        if query.source_version is not None and self.source_version != query.source_version:
            return False
        if query.format is not None and self.format != query.format:
            return False
        if query.text is not None:
            needle = query.text.lower()
            haystack = " ".join(
                value
                for value in (
                    self.asset_id,
                    self.pair_id or "",
                    self.species_code,
                    self.species_name,
                    self.database_title or "",
                    self.relative_path,
                    self.citation,
                )
            ).lower()
            if needle not in haystack:
                return False
        return True

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-ready representation of the entry.

        Returns
        -------
        dict of str to object
            Catalog fields with columns expanded.
        """
        return {
            "id": self.asset_id,
            "pair_id": self.pair_id,
            "kind": self.kind,
            "format": self.format,
            "evidence": self.evidence,
            "publication": self.publication,
            "source_model": self.source_model,
            "source_version": self.source_version,
            "source_build": self.source_build,
            "database_title": self.database_title,
            "relative_path": self.relative_path,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "species_code": self.species_code,
            "species_name": self.species_name,
            "site_from": self.site_from,
            "site_to": self.site_to,
            "pnc": self.pnc,
            "stock_height_m": self.stock_height_m,
            "stock_age_years": self.stock_age_years,
            "pct_height_m": self.pct_height_m,
            "ct_height_m": self.ct_height_m,
            "field_count": self.field_count,
            "data_rows": self.data_rows,
            "run_count": self.run_count,
            "first_age": self.first_age,
            "last_age": self.last_age,
            "treatments": list(self.treatments),
            "columns": [
                {
                    "position": column.position,
                    "name": column.name,
                    "units": column.units,
                    "evidence": column.evidence,
                    "confidence": column.confidence,
                }
                for column in self.columns
            ],
            "columns_ref": self.columns_ref,
            "column_count": self.column_count,
            "citation": self.citation,
            "validation_status": self.validation_status,
            "validation_warnings": list(self.validation_warnings),
        }


def _mapping(value: object, label: str) -> dict[str, object]:
    """Convert a JSON object to a string-keyed mapping.

    Parameters
    ----------
    value : object
        Candidate value.
    label : str
        Location label for errors.

    Returns
    -------
    dict of str to object
        String-keyed mapping.

    Raises
    ------
    CatalogError
        When the value is not an object.
    """
    if not isinstance(value, dict):
        message = f"{label} must be an object"
        raise CatalogError(message)
    return {str(key): item for key, item in value.items()}


def _string(mapping: dict[str, object], key: str, label: str) -> str:
    """Read a required string.

    Parameters
    ----------
    mapping : dict of str to object
        Source mapping.
    key : str
        Key to read.
    label : str
        Location label for errors.

    Returns
    -------
    str
        The string value.

    Raises
    ------
    CatalogError
        When the key is missing or not a string.
    """
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        message = f"{label}.{key} must be a non-empty string"
        raise CatalogError(message)
    return value


def _optional_string(mapping: dict[str, object], key: str, label: str) -> str | None:
    """Read an optional string.

    Parameters
    ----------
    mapping : dict of str to object
        Source mapping.
    key : str
        Key to read.
    label : str
        Location label for errors.

    Returns
    -------
    str or None
        The string value, or ``None``.

    Raises
    ------
    CatalogError
        When the value is present and not a string.
    """
    value = mapping.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        message = f"{label}.{key} must be a string"
        raise CatalogError(message)
    return value


def _int(mapping: dict[str, object], key: str, label: str) -> int:
    """Read a required integer.

    Parameters
    ----------
    mapping : dict of str to object
        Source mapping.
    key : str
        Key to read.
    label : str
        Location label for errors.

    Returns
    -------
    int
        The integer value.

    Raises
    ------
    CatalogError
        When the key is missing or not an integer.
    """
    value = mapping.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        message = f"{label}.{key} must be an integer"
        raise CatalogError(message)
    return value


def _optional_int(mapping: dict[str, object], key: str, label: str) -> int | None:
    """Read an optional integer.

    Parameters
    ----------
    mapping : dict of str to object
        Source mapping.
    key : str
        Key to read.
    label : str
        Location label for errors.

    Returns
    -------
    int or None
        The integer value, or ``None``.

    Raises
    ------
    CatalogError
        When the value is present and not an integer.
    """
    value = mapping.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        message = f"{label}.{key} must be an integer"
        raise CatalogError(message)
    return value


def _optional_float(mapping: dict[str, object], key: str, label: str) -> float | None:
    """Read an optional number.

    Parameters
    ----------
    mapping : dict of str to object
        Source mapping.
    key : str
        Key to read.
    label : str
        Location label for errors.

    Returns
    -------
    float or None
        The number value, or ``None``.

    Raises
    ------
    CatalogError
        When the value is present and not a number.
    """
    value = mapping.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        message = f"{label}.{key} must be a number"
        raise CatalogError(message)
    return float(value)


def _string_list(mapping: dict[str, object], key: str, label: str) -> tuple[str, ...]:
    """Read an optional list of strings.

    Parameters
    ----------
    mapping : dict of str to object
        Source mapping.
    key : str
        Key to read.
    label : str
        Location label for errors.

    Returns
    -------
    tuple of str
        The strings, or an empty tuple.

    Raises
    ------
    CatalogError
        When the value is present and not a list of strings.
    """
    value = mapping.get(key, [])
    if not isinstance(value, list):
        message = f"{label}.{key} must be a list"
        raise CatalogError(message)
    items: list[str] = []
    for item in value:
        if not isinstance(item, str):
            message = f"{label}.{key} items must be strings"
            raise CatalogError(message)
        items.append(item)
    return tuple(items)


def _parse_entry(asset: dict[str, object], index: int) -> CatalogEntry:
    """Parse one manifest asset into a catalog entry.

    Parameters
    ----------
    asset : dict of str to object
        Manifest asset object.
    index : int
        Asset index for error labels.

    Returns
    -------
    CatalogEntry
        The catalog entry.

    Raises
    ------
    CatalogError
        When a required field is missing or invalid.
    """
    label = f"assets[{index}]"
    source = _mapping(asset.get("source"), f"{label}.source")
    table = _mapping(asset.get("table"), f"{label}.table")
    metadata = _mapping(asset.get("metadata"), f"{label}.metadata")
    validation = _mapping(asset.get("validation"), f"{label}.validation")
    table_format = _string(table, "format", f"{label}.table")
    columns = load_columns(table_format)
    field_count = _int(table, "field_count", f"{label}.table")
    if field_count != len(columns):
        message = f"{label}.table.field_count {field_count} does not match {len(columns)} columns"
        raise CatalogError(message)
    site_from = _int(metadata, "site_from", f"{label}.metadata")
    site_to = _int(metadata, "site_to", f"{label}.metadata")
    if site_from > site_to:
        message = f"{label}.metadata site range is inverted"
        raise CatalogError(message)
    pnc = _string(metadata, "pnc", f"{label}.metadata")
    if pnc not in _PNC_VALUES:
        message = f"{label}.metadata.pnc must be C, N, or P"
        raise CatalogError(message)
    column_count = _optional_int(asset, "column_count", label)
    return CatalogEntry(
        asset_id=_string(asset, "id", label),
        pair_id=_optional_string(table, "pair_id", f"{label}.table"),
        kind=_string(asset, "kind", label),
        format=table_format,
        evidence=_string(asset, "evidence", label),
        publication=_string(asset, "publication", label),
        source_model=_string(source, "model", f"{label}.source"),
        source_version=_string(source, "version", f"{label}.source"),
        source_build=_optional_string(source, "build", f"{label}.source"),
        database_title=_optional_string(source, "database_title", f"{label}.source"),
        relative_path=_string(source, "relative_path", f"{label}.source"),
        sha256=_string(source, "sha256", f"{label}.source"),
        size_bytes=_int(source, "size_bytes", f"{label}.source"),
        species_code=_string(metadata, "species_code", f"{label}.metadata").upper(),
        species_name=_string(metadata, "species_name", f"{label}.metadata"),
        site_from=site_from,
        site_to=site_to,
        pnc=pnc,
        stock_height_m=_optional_float(metadata, "stock_height_m", f"{label}.metadata"),
        stock_age_years=_optional_float(metadata, "stock_age_years", f"{label}.metadata"),
        pct_height_m=_optional_int(metadata, "pct_height_m", f"{label}.metadata"),
        ct_height_m=_optional_int(metadata, "ct_height_m", f"{label}.metadata"),
        field_count=field_count,
        data_rows=_int(table, "data_rows", f"{label}.table"),
        run_count=_int(table, "run_count", f"{label}.table"),
        first_age=_optional_float(table, "first_age", f"{label}.table"),
        last_age=_optional_float(table, "last_age", f"{label}.table"),
        treatments=_string_list(table, "treatments", f"{label}.table"),
        columns=columns,
        columns_ref=_optional_string(asset, "columns_ref", label),
        column_count=column_count if column_count is not None else len(columns),
        citation=_string(asset, "citation", label),
        validation_status=_string(validation, "status", f"{label}.validation"),
        validation_warnings=_string_list(validation, "warnings", f"{label}.validation"),
    )


@dataclass(frozen=True)
class TableCatalog:
    """An in-memory table catalog.

    Parameters
    ----------
    entries : tuple of CatalogEntry
        Catalog entries.
    """

    entries: tuple[CatalogEntry, ...]

    @classmethod
    def from_manifest(cls, path: Path) -> TableCatalog:
        """Load a catalog from a manifest file.

        Parameters
        ----------
        path : Path
            Manifest JSON path.

        Returns
        -------
        TableCatalog
            The loaded catalog.

        Raises
        ------
        OSError
            When the file cannot be read.
        CatalogError
            When the manifest is malformed.
        """
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            message = f"manifest is not valid JSON: {path}"
            raise CatalogError(message) from exc
        return cls.from_manifest_data(data)

    @classmethod
    def from_manifest_data(cls, data: object) -> TableCatalog:
        """Load a catalog from manifest data.

        Parameters
        ----------
        data : object
            Parsed manifest object.

        Returns
        -------
        TableCatalog
            The loaded catalog.

        Raises
        ------
        CatalogError
            When the manifest is malformed.
        """
        manifest = _mapping(data, "manifest")
        assets = manifest.get("assets")
        if not isinstance(assets, list):
            message = "manifest.assets must be a list"
            raise CatalogError(message)
        entries: list[CatalogEntry] = []
        for index, asset_value in enumerate(assets):
            asset = _mapping(asset_value, f"assets[{index}]")
            if _string(asset, "kind", f"assets[{index}]") != "tipsy_table":
                continue
            entries.append(_parse_entry(asset, index))
        return cls(tuple(entries))

    def get(self, asset_id: str) -> CatalogEntry | None:
        """Return one entry by asset ID.

        Parameters
        ----------
        asset_id : str
            Stable asset ID.

        Returns
        -------
        CatalogEntry or None
            The matching entry, or ``None``.
        """
        for entry in self.entries:
            if entry.asset_id == asset_id:
                return entry
        return None

    def search(self, query: CatalogQuery | None = None) -> tuple[CatalogEntry, ...]:
        """Return entries matching a query.

        Parameters
        ----------
        query : CatalogQuery or None, optional
            Query filters. ``None`` returns every entry.

        Returns
        -------
        tuple of CatalogEntry
            Matching entries in manifest order.
        """
        effective = query if query is not None else CatalogQuery()
        return tuple(entry for entry in self.entries if entry.matches(effective))

    def __len__(self) -> int:
        """Return the number of catalog entries."""
        return len(self.entries)

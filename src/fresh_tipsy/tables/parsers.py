"""Parser for compact TIPSY ``.tab`` tables."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from fresh_tipsy.tables.errors import TableFormatError
from fresh_tipsy.tables.formats import TAB_FIELD_COUNT, TABLE_HEADER_MARKER
from fresh_tipsy.tables.metadata import FilenameMetadata, parse_filename, slugify

_RUN_RE: re.Pattern[str] = re.compile(r"^\[RUN,(?P<initial>\d+),(?P<pct>\d+),(?P<ct>\d+)\]$")
_REQUIRED_HEADER_KEYS: tuple[str, ...] = (
    "DatabaseTitle",
    "File",
    "SpeciesName",
    "Source",
    "Code",
    "SiteFrom",
    "SiteTo",
    "TASSsiteIndex",
    "TASSsiteSpecies",
    "PNC",
)
_KNOWN_HEADER_KEYS: frozenset[str] = frozenset(
    (*_REQUIRED_HEADER_KEYS, "PCT", "CT", "StockHt", "StockAge")
)


@dataclass(frozen=True)
class Header:
    """The key/value header block of a TIPSY table.

    Parameters
    ----------
    database_title : str
        Database edition.
    file : str
        Table stem recorded in the header.
    species_name : str
        Species display name.
    source : str
        TASS/SYLVER build and run-date string.
    code : str
        Uppercase species code.
    site_from : int
        Minimum site index.
    site_to : int
        Maximum site index.
    tass_site_index : int
        TASS site-index reference.
    tass_site_species : str
        TASS surrogate species.
    pnc : str
        Planted, natural, or clumped code.
    stock_height_m : float or None
        Planting stock height when present.
    stock_age : float or None
        Planting stock age when present.
    pct_height_m : int or None
        PCT treatment height when present.
    ct_height_m : int or None
        CT treatment height when present.
    extra : tuple of tuple of str
        Unrecognized header keys, sorted by key.
    """

    database_title: str
    file: str
    species_name: str
    source: str
    code: str
    site_from: int
    site_to: int
    tass_site_index: int
    tass_site_species: str
    pnc: str
    stock_height_m: float | None = None
    stock_age: float | None = None
    pct_height_m: int | None = None
    ct_height_m: int | None = None
    extra: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class RunMarker:
    """One ``[RUN,...]`` marker.

    Parameters
    ----------
    initial_density : int
        Stems per hectare at establishment.
    pct_density : int
        Stems per hectare after PCT; ``0`` when absent.
    ct_density : int
        Stems per hectare after CT; ``0`` when absent.
    raw : str
        The original marker line.
    """

    initial_density: int
    pct_density: int
    ct_density: int
    raw: str


@dataclass(frozen=True)
class TableRow:
    """One data row from a TIPSY table.

    Parameters
    ----------
    age : float or None
        Parsed first field, or ``None`` when the field is blank.
    fields : tuple of str
        The raw fields, preserved in source order.
    """

    age: float | None
    fields: tuple[str, ...]


@dataclass(frozen=True)
class RunBlock:
    """One run block and its rows.

    Parameters
    ----------
    marker : RunMarker
        The block marker.
    rows : tuple of TableRow
        Non-empty data rows.
    treatment : str or None
        ``"PCT"``, ``"CT"``, ``"PCT+CT"``, or ``None``.
    boundary_index : int or None
        Zero-based index of the first repeated-age row, which marks the
        post-treatment state.
    """

    marker: RunMarker
    rows: tuple[TableRow, ...]
    treatment: str | None
    boundary_index: int | None


@dataclass(frozen=True)
class TabTable:
    """A parsed compact TIPSY ``.tab`` table.

    Parameters
    ----------
    path : Path
        Source path.
    header : Header
        Parsed header.
    filename : FilenameMetadata
        Metadata inferred from the filename.
    blocks : tuple of RunBlock
        Run blocks in source order.
    field_count : int
        Field count per data row.
    sha256 : str
        Source SHA-256.
    size_bytes : int
        Source size in bytes.
    warnings : tuple of str
        Metadata reconciliation warnings.
    """

    path: Path
    header: Header
    filename: FilenameMetadata
    blocks: tuple[RunBlock, ...]
    field_count: int
    sha256: str
    size_bytes: int
    warnings: tuple[str, ...] = ()

    @property
    def data_rows(self) -> int:
        """Return the total number of non-empty data rows."""
        return sum(len(block.rows) for block in self.blocks)

    @property
    def run_count(self) -> int:
        """Return the number of run blocks."""
        return len(self.blocks)

    @property
    def first_age(self) -> float | None:
        """Return the smallest non-empty age, or ``None``."""
        ages = [row.age for block in self.blocks for row in block.rows if row.age is not None]
        return min(ages) if ages else None

    @property
    def last_age(self) -> float | None:
        """Return the largest non-empty age, or ``None``."""
        ages = [row.age for block in self.blocks for row in block.rows if row.age is not None]
        return max(ages) if ages else None

    @property
    def pair_id(self) -> str:
        """Return the stable pair ID for this table and its ``.taf`` partner."""
        return f"tipsy45-{slugify(self.path.stem)}"

    @property
    def asset_id(self) -> str:
        """Return the stable manifest ID for this ``.tab`` asset."""
        return f"tipsy45-db-{slugify(self.path.stem)}-tab"

    @property
    def treatments(self) -> tuple[str, ...]:
        """Return the treatment labels present in source order."""
        labels: list[str] = []
        for block in self.blocks:
            if block.treatment is not None and block.treatment not in labels:
                labels.append(block.treatment)
        return tuple(labels)


def _required(values: dict[str, str], key: str) -> str:
    """Return a required header value or raise a format error.

    Parameters
    ----------
    values : dict of str to str
        Header key/value pairs.
    key : str
        Required key.

    Returns
    -------
    str
        The stripped value.

    Raises
    ------
    TableFormatError
        When the key is missing.
    """
    try:
        return values[key]
    except KeyError as exc:
        message = f"missing required header key: {key}"
        raise TableFormatError(message) from exc


def _int_value(values: dict[str, str], key: str) -> int:
    """Parse an integer header value.

    Parameters
    ----------
    values : dict of str to str
        Header key/value pairs.
    key : str
        Required key.

    Returns
    -------
    int
        Parsed integer.

    Raises
    ------
    TableFormatError
        When the value is not an integer.
    """
    raw = _required(values, key)
    try:
        return int(raw)
    except ValueError as exc:
        message = f"header key {key} is not an integer: {raw!r}"
        raise TableFormatError(message) from exc


def _optional_int(values: dict[str, str], key: str) -> int | None:
    """Parse an optional integer header value.

    Parameters
    ----------
    values : dict of str to str
        Header key/value pairs.
    key : str
        Optional key.

    Returns
    -------
    int or None
        Parsed integer, or ``None`` when the key is absent or blank.
    """
    raw = values.get(key, "").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError as exc:
        message = f"header key {key} is not an integer: {raw!r}"
        raise TableFormatError(message) from exc


def _optional_float(values: dict[str, str], key: str) -> float | None:
    """Parse an optional floating-point header value.

    Parameters
    ----------
    values : dict of str to str
        Header key/value pairs.
    key : str
        Optional key.

    Returns
    -------
    float or None
        Parsed float, or ``None`` when the key is absent or blank.
    """
    raw = values.get(key, "").strip()
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError as exc:
        message = f"header key {key} is not a number: {raw!r}"
        raise TableFormatError(message) from exc


def _build_header(values: dict[str, str]) -> Header:
    """Build a typed header from key/value pairs.

    Parameters
    ----------
    values : dict of str to str
        Header key/value pairs.

    Returns
    -------
    Header
        The typed header.

    Raises
    ------
    TableFormatError
        When a required key is missing or a value is invalid.
    """
    pnc = _required(values, "PNC").upper()
    if pnc not in {"C", "N", "P"}:
        message = f"header PNC is not C, N, or P: {pnc!r}"
        raise TableFormatError(message)
    site_from = _int_value(values, "SiteFrom")
    site_to = _int_value(values, "SiteTo")
    if site_from > site_to:
        message = f"header site range is inverted: {site_from} > {site_to}"
        raise TableFormatError(message)
    extra = tuple((key, values[key]) for key in sorted(values) if key not in _KNOWN_HEADER_KEYS)
    return Header(
        database_title=_required(values, "DatabaseTitle"),
        file=_required(values, "File"),
        species_name=_required(values, "SpeciesName"),
        source=_required(values, "Source"),
        code=_required(values, "Code").upper(),
        site_from=site_from,
        site_to=site_to,
        tass_site_index=_int_value(values, "TASSsiteIndex"),
        tass_site_species=_required(values, "TASSsiteSpecies"),
        pnc=pnc,
        stock_height_m=_optional_float(values, "StockHt"),
        stock_age=_optional_float(values, "StockAge"),
        pct_height_m=_optional_int(values, "PCT"),
        ct_height_m=_optional_int(values, "CT"),
        extra=extra,
    )


def parse_header(lines: Sequence[str]) -> tuple[Header, int]:
    """Parse the header block of a TIPSY table.

    Parameters
    ----------
    lines : sequence of str
        File lines without line endings.

    Returns
    -------
    tuple of (Header, int)
        The typed header and the index of the first ``[RUN,...]`` line.

    Raises
    ------
    TableFormatError
        When the file is empty, lacks the marker, lacks a required key, or
        contains an invalid value.
    """
    if not lines or lines[0].strip() != TABLE_HEADER_MARKER:
        message = f"file does not start with {TABLE_HEADER_MARKER}"
        raise TableFormatError(message)
    values: dict[str, str] = {}
    for index, line in enumerate(lines[1:], start=1):
        text = line.strip()
        if text.startswith("[RUN"):
            return _build_header(values), index
        if not text:
            continue
        if "=" not in text:
            message = f"header line {index + 1} is not key=value: {line!r}"
            raise TableFormatError(message)
        key, value = text.split("=", 1)
        values[key.strip()] = value.strip()
    message = "file has no [RUN,...] marker"
    raise TableFormatError(message)


def parse_run_marker(line: str) -> RunMarker:
    """Parse one ``[RUN,...]`` marker.

    Parameters
    ----------
    line : str
        Marker line.

    Returns
    -------
    RunMarker
        The parsed marker.

    Raises
    ------
    TableFormatError
        When the line does not match the marker grammar.
    """
    match = _RUN_RE.fullmatch(line.strip())
    if match is None:
        message = f"invalid [RUN,...] marker: {line!r}"
        raise TableFormatError(message)
    return RunMarker(
        initial_density=int(match.group("initial")),
        pct_density=int(match.group("pct")),
        ct_density=int(match.group("ct")),
        raw=line.strip(),
    )


def _parse_age(raw: str) -> float | None:
    """Parse the age field.

    Parameters
    ----------
    raw : str
        Raw first field.

    Returns
    -------
    float or None
        Parsed age, or ``None`` when blank.

    Raises
    ------
    TableFormatError
        When the field is not numeric.
    """
    text = raw.strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError as exc:
        message = f"age field is not numeric: {raw!r}"
        raise TableFormatError(message) from exc


def _treatment_label(marker: RunMarker) -> str | None:
    """Return the treatment label for a marker.

    Parameters
    ----------
    marker : RunMarker
        Block marker.

    Returns
    -------
    str or None
        ``"PCT"``, ``"CT"``, ``"PCT+CT"``, or ``None``.
    """
    has_pct = marker.pct_density > 0
    has_ct = marker.ct_density > 0
    if has_pct and has_ct:
        return "PCT+CT"
    if has_pct:
        return "PCT"
    if has_ct:
        return "CT"
    return None


def _parse_block(marker: RunMarker, lines: Sequence[str]) -> RunBlock:
    """Parse one run block.

    Parameters
    ----------
    marker : RunMarker
        Block marker.
    lines : sequence of str
        Lines after the marker and before the next marker.

    Returns
    -------
    RunBlock
        The parsed block.

    Raises
    ------
    TableFormatError
        When a data row has the wrong field count or the block is empty.
    """
    rows: list[TableRow] = []
    for line in lines:
        if not line.strip():
            continue
        fields = tuple(line.split("\t"))
        if len(fields) != TAB_FIELD_COUNT:
            message = (
                f"data row has {len(fields)} fields, expected {TAB_FIELD_COUNT}: {line[:80]!r}"
            )
            raise TableFormatError(message)
        rows.append(TableRow(age=_parse_age(fields[0]), fields=fields))
    if not rows:
        message = f"run block has no data rows: {marker.raw}"
        raise TableFormatError(message)
    boundary_index: int | None = None
    previous_age: float | None = None
    for index, row in enumerate(rows):
        if previous_age is not None and row.age == previous_age:
            boundary_index = index
            break
        previous_age = row.age
    return RunBlock(
        marker=marker,
        rows=tuple(rows),
        treatment=_treatment_label(marker),
        boundary_index=boundary_index,
    )


def _compare_metadata(header: Header, filename: FilenameMetadata, stem: str) -> tuple[str, ...]:
    """Compare header and filename metadata.

    Parameters
    ----------
    header : Header
        Parsed header.
    filename : FilenameMetadata
        Parsed filename metadata.
    stem : str
        Filename stem.

    Returns
    -------
    tuple of str
        Reconciliation warnings, empty when the metadata agrees.
    """
    warnings: list[str] = []
    if header.file != stem:
        warnings.append(f"header File {header.file!r} differs from filename {stem!r}")
    if header.code != filename.species_code:
        warnings.append(
            f"header Code {header.code!r} differs from filename {filename.species_code!r}"
        )
    if (header.site_from, header.site_to) != (filename.site_from, filename.site_to):
        warnings.append(
            "header site range "
            f"{header.site_from}-{header.site_to} differs from filename "
            f"{filename.site_from}-{filename.site_to}"
        )
    if header.pnc != filename.pnc:
        warnings.append(f"header PNC {header.pnc!r} differs from filename {filename.pnc!r}")
    if (header.pct_height_m or 0) != filename.pct_code:
        warnings.append(
            f"header PCT {header.pct_height_m!r} differs from filename code {filename.pct_code}"
        )
    if header.ct_height_m != filename.ct_code:
        warnings.append(
            f"header CT {header.ct_height_m!r} differs from filename code {filename.ct_code!r}"
        )
    return tuple(warnings)


def parse_tab_file(path: Path) -> TabTable:
    """Parse a compact TIPSY ``.tab`` table.

    Parameters
    ----------
    path : Path
        Source file.

    Returns
    -------
    TabTable
        The parsed table.

    Raises
    ------
    TableFormatError
        When the file is not ASCII, malformed, or has an invalid field count.
    OSError
        When the file cannot be read.
    """
    raw = path.read_bytes()
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as exc:
        message = f"table is not ASCII: {path}"
        raise TableFormatError(message) from exc
    lines = text.splitlines()
    header, first_run = parse_header(lines)
    filename = parse_filename(path.stem)
    blocks: list[RunBlock] = []
    marker: RunMarker | None = None
    block_lines: list[str] = []
    for line in lines[first_run:]:
        if line.startswith("[RUN"):
            if marker is not None:
                blocks.append(_parse_block(marker, block_lines))
            marker = parse_run_marker(line)
            block_lines = []
        elif marker is not None:
            block_lines.append(line)
    if marker is not None:
        blocks.append(_parse_block(marker, block_lines))
    if not blocks:
        message = f"file has no run blocks: {path}"
        raise TableFormatError(message)
    return TabTable(
        path=path,
        header=header,
        filename=filename,
        blocks=tuple(blocks),
        field_count=TAB_FIELD_COUNT,
        sha256=hashlib.sha256(raw).hexdigest(),
        size_bytes=len(raw),
        warnings=_compare_metadata(header, filename, path.stem),
    )

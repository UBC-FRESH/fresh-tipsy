"""TIPSY table readers and metadata."""

from __future__ import annotations

from fresh_tipsy.tables.catalog import CatalogEntry, CatalogError, CatalogQuery, TableCatalog
from fresh_tipsy.tables.columns import load_columns
from fresh_tipsy.tables.errors import TableFormatError
from fresh_tipsy.tables.formats import (
    TAB_COLUMNS,
    TAB_FIELD_COUNT,
    TAF_COLUMNS_REF,
    TAF_FIELD_COUNT,
    ColumnSpec,
)
from fresh_tipsy.tables.manifest import build_tab_manifest_entry, build_taf_manifest_entry
from fresh_tipsy.tables.metadata import FilenameMetadata, parse_filename, slugify
from fresh_tipsy.tables.parsers import (
    Header,
    PairTable,
    RunBlock,
    RunMarker,
    TableRow,
    TIPSYTable,
    parse_header,
    parse_pair,
    parse_run_marker,
    parse_tab_file,
    parse_taf_file,
)

__all__ = [
    "TAB_COLUMNS",
    "TAB_FIELD_COUNT",
    "TAF_COLUMNS_REF",
    "TAF_FIELD_COUNT",
    "CatalogEntry",
    "CatalogError",
    "CatalogQuery",
    "ColumnSpec",
    "FilenameMetadata",
    "Header",
    "PairTable",
    "RunBlock",
    "RunMarker",
    "TIPSYTable",
    "TableCatalog",
    "TableFormatError",
    "TableRow",
    "build_tab_manifest_entry",
    "build_taf_manifest_entry",
    "load_columns",
    "parse_filename",
    "parse_header",
    "parse_pair",
    "parse_run_marker",
    "parse_tab_file",
    "parse_taf_file",
    "slugify",
]

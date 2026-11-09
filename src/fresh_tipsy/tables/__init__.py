"""TIPSY table readers and metadata."""

from __future__ import annotations

from fresh_tipsy.tables.errors import TableFormatError
from fresh_tipsy.tables.formats import TAB_COLUMNS, TAB_FIELD_COUNT, ColumnSpec
from fresh_tipsy.tables.manifest import build_tab_manifest_entry
from fresh_tipsy.tables.metadata import FilenameMetadata, parse_filename, slugify
from fresh_tipsy.tables.parsers import (
    Header,
    RunBlock,
    RunMarker,
    TableRow,
    TabTable,
    parse_header,
    parse_run_marker,
    parse_tab_file,
)

__all__ = [
    "TAB_COLUMNS",
    "TAB_FIELD_COUNT",
    "ColumnSpec",
    "FilenameMetadata",
    "Header",
    "RunBlock",
    "RunMarker",
    "TabTable",
    "TableFormatError",
    "TableRow",
    "build_tab_manifest_entry",
    "parse_filename",
    "parse_header",
    "parse_run_marker",
    "parse_tab_file",
    "slugify",
]

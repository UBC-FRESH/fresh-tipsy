"""Format constants and column specifications for TIPSY tables."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

TAB_FIELD_COUNT: Final[int] = 22
TAF_FIELD_COUNT: Final[int] = 151
TABLE_HEADER_MARKER: Final[str] = "[TASS SPECIES]"


@dataclass(frozen=True)
class ColumnSpec:
    """One TIPSY table column.

    Parameters
    ----------
    position : int
        Zero-based field position.
    name : str
        Column name from ``OutputColumns.txt``.
    units : str
        Source unit string.
    evidence : str
        Evidence label for the column.
    confidence : str
        Confidence in the column mapping.
    """

    position: int
    name: str
    units: str
    evidence: str
    confidence: str


TAB_COLUMNS: Final[tuple[ColumnSpec, ...]] = (
    ColumnSpec(0, "YearTASS_Base", "yrs", "source_table", "high"),
    ColumnSpec(1, "HeightSindex_Base", "m", "source_table", "high"),
    ColumnSpec(2, "VolumeGross", "m³/ha", "source_table", "high"),
    ColumnSpec(3, "Volume000", "m³/ha", "source_table", "high"),
    ColumnSpec(4, "Volume125", "m³/ha", "source_table", "high"),
    ColumnSpec(5, "Volume175", "m³/ha", "source_table", "high"),
    ColumnSpec(6, "BasalArea000", "m²/ha", "source_table", "high"),
    ColumnSpec(7, "BasalArea125", "m²/ha", "source_table", "high"),
    ColumnSpec(8, "BasalArea175", "m²/ha", "source_table", "high"),
    ColumnSpec(9, "MeanDBHg000", "cm", "source_table", "high"),
    ColumnSpec(10, "MeanDBHg125", "cm", "source_table", "high"),
    ColumnSpec(11, "MeanDBHg175", "cm", "source_table", "high"),
    ColumnSpec(12, "StemCount000", "#/ha", "source_table", "high"),
    ColumnSpec(13, "StemCount125", "#/ha", "source_table", "high"),
    ColumnSpec(14, "StemCount175", "#/ha", "source_table", "high"),
    ColumnSpec(15, "CrownCover", "%", "source_table", "high"),
    ColumnSpec(16, "Crop250VolUtil125", "m³/ha", "source_table", "high"),
    ColumnSpec(17, "Crop250DBHgMean", "cm", "source_table", "high"),
    ColumnSpec(18, "Crop250LiveCrown", "%", "source_table", "high"),
    ColumnSpec(19, "HeightTassTop", "m", "source_table", "high"),
    ColumnSpec(20, "HeightTassMean", "m", "source_table", "high"),
    ColumnSpec(21, "HeightTassPredom", "m", "source_table", "high"),
)

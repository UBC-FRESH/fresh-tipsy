"""Typed request, provenance, and result models for growth queries."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Final

from fresh_tipsy.tables.catalog import CatalogEntry

_PNC_VALUES: Final[frozenset[str]] = frozenset({"C", "N", "P"})
_FORMATS: Final[frozenset[str]] = frozenset({"tab", "taf"})


@dataclass(frozen=True)
class CurveQuery:
    """A growth table query.

    Parameters
    ----------
    species_code : str
        Species code, case-insensitive.
    site_index : float
        Site index to match inside a table's site range.
    age : float or None, optional
        Age in years. Selection does not require it; P3.2 uses it.
    pnc : str or None, optional
        PNC filter.
    stock_height_m : float or None, optional
        Exact stock-height filter.
    source_version : str or None, optional
        Source model version filter.
    format : str, optional
        ``"tab"`` or ``"taf"``. Defaults to the compact table.
    """

    species_code: str
    site_index: float
    age: float | None = None
    pnc: str | None = None
    stock_height_m: float | None = None
    source_version: str | None = None
    format: str = "tab"

    def __post_init__(self) -> None:
        """Validate query fields.

        Raises
        ------
        ValueError
            When a field is empty or out of range.
        """
        if not self.species_code.strip():
            message = "species_code must not be empty"
            raise ValueError(message)
        if not math.isfinite(self.site_index):
            message = "site_index must be finite"
            raise ValueError(message)
        if self.age is not None and (not math.isfinite(self.age) or self.age < 0):
            message = "age must be a finite non-negative number"
            raise ValueError(message)
        if self.stock_height_m is not None and (
            not math.isfinite(self.stock_height_m) or self.stock_height_m < 0
        ):
            message = "stock_height_m must be a finite non-negative number"
            raise ValueError(message)
        if self.pnc is not None and self.pnc.upper() not in _PNC_VALUES:
            message = "pnc must be C, N, or P"
            raise ValueError(message)
        if self.format not in _FORMATS:
            message = "format must be tab or taf"
            raise ValueError(message)


@dataclass(frozen=True)
class Provenance:
    """Source provenance for a selected table or query result.

    Parameters
    ----------
    asset_id : str
        Stable manifest asset ID.
    pair_id : str or None
        Shared `.tab`/`.taf` pair ID.
    format : str
        Source table format.
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
    evidence : str
        Evidence label.
    citation : str
        Source citation.
    """

    asset_id: str
    pair_id: str | None
    format: str
    source_model: str
    source_version: str
    source_build: str | None
    database_title: str | None
    relative_path: str
    sha256: str
    evidence: str
    citation: str

    @classmethod
    def from_entry(cls, entry: CatalogEntry) -> Provenance:
        """Build provenance from a catalog entry.

        Parameters
        ----------
        entry : CatalogEntry
            Selected catalog entry.

        Returns
        -------
        Provenance
            Provenance for the entry.
        """
        return cls(
            asset_id=entry.asset_id,
            pair_id=entry.pair_id,
            format=entry.format,
            source_model=entry.source_model,
            source_version=entry.source_version,
            source_build=entry.source_build,
            database_title=entry.database_title,
            relative_path=entry.relative_path,
            sha256=entry.sha256,
            evidence=entry.evidence,
            citation=entry.citation,
        )

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-ready provenance mapping.

        Returns
        -------
        dict of str to object
            Provenance fields.
        """
        return {
            "asset_id": self.asset_id,
            "pair_id": self.pair_id,
            "format": self.format,
            "source_model": self.source_model,
            "source_version": self.source_version,
            "source_build": self.source_build,
            "database_title": self.database_title,
            "relative_path": self.relative_path,
            "sha256": self.sha256,
            "evidence": self.evidence,
            "citation": self.citation,
        }


@dataclass(frozen=True)
class TableSelection:
    """The table selected for a growth query.

    Parameters
    ----------
    entry : CatalogEntry
        Selected catalog entry.
    query : CurveQuery
        Original query.
    provenance : Provenance
        Source provenance.
    rationale : str
        Human-readable selection rationale.
    alternatives : tuple of str
        Other candidate asset IDs.
    """

    entry: CatalogEntry
    query: CurveQuery
    provenance: Provenance
    rationale: str
    alternatives: tuple[str, ...] = field(default_factory=tuple)

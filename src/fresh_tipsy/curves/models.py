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
    scenario : str or None, optional
        ``None``, ``"untreated"``, ``"PCT"``, ``"CT"``, or ``"PCT+CT"``.
    initial_density : int or None, optional
        Initial-density filter for a run block.
    pct_density : int or None, optional
        Post-PCT density filter for a run block.
    ct_density : int or None, optional
        Post-CT density filter for a run block.
    format : str, optional
        ``"tab"`` or ``"taf"``. Defaults to the compact table.
    """

    species_code: str
    site_index: float
    age: float | None = None
    pnc: str | None = None
    stock_height_m: float | None = None
    source_version: str | None = None
    scenario: str | None = None
    initial_density: int | None = None
    pct_density: int | None = None
    ct_density: int | None = None
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
        if self.scenario is not None and self.scenario.upper() not in {
            "UNTREATED",
            "PCT",
            "CT",
            "PCT+CT",
        }:
            message = "scenario must be untreated, PCT, CT, or PCT+CT"
            raise ValueError(message)
        for name, density in (
            ("initial_density", self.initial_density),
            ("pct_density", self.pct_density),
            ("ct_density", self.ct_density),
        ):
            if density is not None and density < 0:
                message = f"{name} must be non-negative"
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


@dataclass(frozen=True)
class InterpolatedRow:
    """One age row from a selected run block.

    Parameters
    ----------
    age : float
        Requested age.
    values : tuple of float or None
        Non-age values in column order, after interpolation.
    lower_age : float
        Lower bracketing source age.
    upper_age : float
        Upper bracketing source age.
    fraction : float
        Interpolation fraction between the two ages.
    scenario : str
        ``"untreated"`` or the treatment label.
    block_index : int
        Source block index.
    initial_density : int
        Block initial density.
    pct_density : int
        Block post-PCT density.
    ct_density : int
        Block post-CT density.
    """

    age: float
    values: tuple[float | None, ...]
    lower_age: float
    upper_age: float
    fraction: float
    scenario: str
    block_index: int
    initial_density: int
    pct_density: int
    ct_density: int


@dataclass(frozen=True)
class QueryResult:
    """A selected table and its interpolated row.

    Parameters
    ----------
    selection : TableSelection
        Selected source table.
    row : InterpolatedRow
        Interpolated row.
    """

    selection: TableSelection
    row: InterpolatedRow


@dataclass(frozen=True)
class CurvePoint:
    """Typed metric values at one age.

    Parameters
    ----------
    age : float
        Query age.
    format : str
        Source table format.
    volume_gross_m3_ha : float or None
        Gross volume.
    volume_total_m3_ha : float or None
        Total standing volume.
    volume_merch_m3_ha : float or None
        Merchantable volume.
    height_site_m : float or None
        Site height.
    height_top_m : float or None
        TASS top height.
    height_mean_m : float or None
        TASS mean height.
    height_predominant_m : float or None
        TASS predominant height.
    dbh_cm : float or None
        Quadratic mean DBH.
    stems_per_ha : float or None
        Live stems per hectare.
    basal_area_m2_ha : float or None
        Basal area.
    crown_cover_pct : float or None
        Crown cover.
    biomass_live_odt_ha : float or None
        Live biomass.
    biomass_dead_odt_ha : float or None
        Dead biomass.
    carbon_live_t_ha : float or None
        Live carbon.
    carbon_dead_t_ha : float or None
        Dead carbon.
    scenario : str
        Scenario label.
    lower_age : float
        Lower bracketing age.
    upper_age : float
        Upper bracketing age.
    fraction : float
        Interpolation fraction.
    provenance : Provenance
        Source provenance.
    unavailable_metrics : tuple of str
        Metrics not available in this source format.
    """

    age: float
    format: str
    volume_gross_m3_ha: float | None
    volume_total_m3_ha: float | None
    volume_merch_m3_ha: float | None
    height_site_m: float | None
    height_top_m: float | None
    height_mean_m: float | None
    height_predominant_m: float | None
    dbh_cm: float | None
    stems_per_ha: float | None
    basal_area_m2_ha: float | None
    crown_cover_pct: float | None
    biomass_live_odt_ha: float | None
    biomass_dead_odt_ha: float | None
    carbon_live_t_ha: float | None
    carbon_dead_t_ha: float | None
    scenario: str
    lower_age: float
    upper_age: float
    fraction: float
    provenance: Provenance
    unavailable_metrics: tuple[str, ...]


@dataclass(frozen=True)
class MetricValue:
    """One metric value with its units and evidence.

    Parameters
    ----------
    metric : str
        Metric name.
    value : float
        Metric value.
    units : str
        Source unit.
    evidence : str
        Evidence label.
    age : float
        Query age.
    scenario : str
        Scenario label.
    provenance : Provenance
        Source provenance.
    """

    metric: str
    value: float
    units: str
    evidence: str
    age: float
    scenario: str
    provenance: Provenance

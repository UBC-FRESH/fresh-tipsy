"""Metric definitions and typed point construction."""

from __future__ import annotations

import math
from dataclasses import dataclass

from fresh_tipsy.curves.models import CurvePoint, QueryResult
from fresh_tipsy.tables.columns import load_columns


@dataclass(frozen=True)
class MetricSpec:
    """Definition of one queryable metric.

    Parameters
    ----------
    name : str
        Metric name.
    field : str
        ``CurvePoint`` field name.
    units : str
        Source unit.
    formats : tuple of str
        Formats that provide the metric.
    evidence : tuple of tuple of str
        ``(format, evidence)`` pairs.
    description : str
        Human-readable definition.
    """

    name: str
    field: str
    units: str
    formats: tuple[str, ...]
    evidence: tuple[tuple[str, str], ...]
    description: str

    def evidence_for(self, table_format: str) -> str:
        """Return the evidence label for a format.

        Parameters
        ----------
        table_format : str
            ``"tab"`` or ``"taf"``.

        Returns
        -------
        str
            Evidence label.

        Raises
        ------
        KeyError
            When the format has no declared evidence.
        """
        return dict(self.evidence)[table_format]


METRICS: dict[str, MetricSpec] = {
    "volume_gross": MetricSpec(
        "volume_gross",
        "volume_gross_m3_ha",
        "m³/ha",
        ("tab",),
        (("tab", "source_table"),),
        "Gross whole-stand volume.",
    ),
    "volume_total": MetricSpec(
        "volume_total",
        "volume_total_m3_ha",
        "m³/ha",
        ("tab",),
        (("tab", "source_table"),),
        "Total standing volume.",
    ),
    "volume_merch": MetricSpec(
        "volume_merch",
        "volume_merch_m3_ha",
        "m³/ha",
        ("tab", "taf"),
        (("tab", "source_table"), ("taf", "reimplemented")),
        "Merchantable volume; `.taf` sums the diameter-class volume columns.",
    ),
    "height_site": MetricSpec(
        "height_site",
        "height_site_m",
        "m",
        ("tab", "taf"),
        (("tab", "source_table"), ("taf", "source_table")),
        "Site height.",
    ),
    "height_top": MetricSpec(
        "height_top",
        "height_top_m",
        "m",
        ("tab",),
        (("tab", "source_table"),),
        "TASS top height.",
    ),
    "height_mean": MetricSpec(
        "height_mean",
        "height_mean_m",
        "m",
        ("tab",),
        (("tab", "source_table"),),
        "TASS mean height.",
    ),
    "height_predominant": MetricSpec(
        "height_predominant",
        "height_predominant_m",
        "m",
        ("tab",),
        (("tab", "source_table"),),
        "TASS predominant height.",
    ),
    "dbh": MetricSpec(
        "dbh",
        "dbh_cm",
        "cm",
        ("tab", "taf"),
        (("tab", "source_table"), ("taf", "reimplemented")),
        "Quadratic mean DBH; `.taf` derives it from diameter-class stems.",
    ),
    "stems": MetricSpec(
        "stems",
        "stems_per_ha",
        "#/ha",
        ("tab", "taf"),
        (("tab", "source_table"), ("taf", "reimplemented")),
        "Live stems per hectare; `.taf` sums the diameter-class stems.",
    ),
    "basal_area": MetricSpec(
        "basal_area",
        "basal_area_m2_ha",
        "m²/ha",
        ("tab", "taf"),
        (("tab", "source_table"), ("taf", "reimplemented")),
        "Basal area; `.taf` derives it from diameter-class stems.",
    ),
    "crown_cover": MetricSpec(
        "crown_cover",
        "crown_cover_pct",
        "%",
        ("tab",),
        (("tab", "source_table"),),
        "Crown cover.",
    ),
    "biomass_live": MetricSpec(
        "biomass_live",
        "biomass_live_odt_ha",
        "ODT/ha",
        ("taf",),
        (("taf", "reimplemented"),),
        "Live biomass; sums the live component columns.",
    ),
    "biomass_dead": MetricSpec(
        "biomass_dead",
        "biomass_dead_odt_ha",
        "ODT/ha",
        ("taf",),
        (("taf", "reimplemented"),),
        "Dead biomass; sums the dead component columns.",
    ),
    "carbon_live": MetricSpec(
        "carbon_live",
        "carbon_live_t_ha",
        "tonnes/ha",
        (),
        (),
        "Live carbon; no stored carbon columns or documented conversion factor yet.",
    ),
    "carbon_dead": MetricSpec(
        "carbon_dead",
        "carbon_dead_t_ha",
        "tonnes/ha",
        (),
        (),
        "Dead carbon; no stored carbon columns or documented conversion factor yet.",
    ),
}


def _sum_positions(values: tuple[float | None, ...], start: int, end: int) -> float | None:
    """Sum a range of column positions, ignoring blanks.

    Parameters
    ----------
    values : tuple of float or None
        Non-age row values.
    start : int
        First zero-based column position.
    end : int
        Last zero-based column position.

    Returns
    -------
    float or None
        Sum, or ``None`` when every value is blank.
    """
    numbers = [values[position - 1] for position in range(start, end + 1)]
    available = [number for number in numbers if number is not None]
    if not available:
        return None
    return sum(available)


def _stock_metrics(values: tuple[float | None, ...]) -> tuple[float | None, float | None]:
    """Derive basal area and DBH from the diameter-class stems.

    Parameters
    ----------
    values : tuple of float or None
        Non-age row values.

    Returns
    -------
    tuple of (float or None, float or None)
        Basal area and quadratic mean DBH.
    """
    stems = [values[position - 1] for position in range(30, 49)]
    total = sum(value for value in stems if value is not None)
    if total <= 0:
        return (0.0, None)
    basal_area = 0.0
    for index, value in enumerate(stems):
        if value is None:
            continue
        dbh_mid = index * 5
        basal_area += value * math.pi * ((dbh_mid / 200.0) ** 2)
    if basal_area <= 0:
        return (0.0, None)
    dbh_value = 2.0 * math.sqrt((basal_area / total) / math.pi) * 100.0
    return (basal_area, dbh_value)


def build_curve_point(result: QueryResult) -> CurvePoint:
    """Build typed metrics from an interpolated query result.

    Parameters
    ----------
    result : QueryResult
        Selected table and interpolated row.

    Returns
    -------
    CurvePoint
        Typed metric values.
    """
    table_format = result.selection.entry.format
    positions = {column.name: column.position for column in load_columns(table_format)}
    values = result.row.values

    def value(name: str) -> float | None:
        position = positions[name]
        return values[position - 1]

    unavailable = tuple(name for name, spec in METRICS.items() if table_format not in spec.formats)
    volume_gross = value("VolumeGross") if table_format == "tab" else None
    volume_total = value("Volume000") if table_format == "tab" else None
    height_site = value("HeightSindex_Base" if table_format == "tab" else "HeightSindex_Full")
    height_top = value("HeightTassTop") if table_format == "tab" else None
    height_mean = value("HeightTassMean") if table_format == "tab" else None
    height_predominant = value("HeightTassPredom") if table_format == "tab" else None
    crown_cover = value("CrownCover") if table_format == "tab" else None
    if table_format == "tab":
        volume_merch = value("Volume125")
        stems = value("StemCount000")
        basal_area = value("BasalArea000")
        dbh = value("MeanDBHg000")
        biomass_live = None
        biomass_dead = None
    else:
        volume_merch = _sum_positions(values, 49, 67)
        stems = _sum_positions(values, 30, 48)
        basal_area, dbh = _stock_metrics(values)
        biomass_live = _sum_positions(values, 79, 83)
        biomass_dead = _sum_positions(values, 84, 88)
    return CurvePoint(
        age=result.row.age,
        format=table_format,
        volume_gross_m3_ha=volume_gross,
        volume_total_m3_ha=volume_total,
        volume_merch_m3_ha=volume_merch,
        height_site_m=height_site,
        height_top_m=height_top,
        height_mean_m=height_mean,
        height_predominant_m=height_predominant,
        dbh_cm=dbh,
        stems_per_ha=stems,
        basal_area_m2_ha=basal_area,
        crown_cover_pct=crown_cover,
        biomass_live_odt_ha=biomass_live,
        biomass_dead_odt_ha=biomass_dead,
        carbon_live_t_ha=None,
        carbon_dead_t_ha=None,
        scenario=result.row.scenario,
        lower_age=result.row.lower_age,
        upper_age=result.row.upper_age,
        fraction=result.row.fraction,
        provenance=result.selection.provenance,
        unavailable_metrics=unavailable,
    )

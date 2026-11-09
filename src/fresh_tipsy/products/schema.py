"""Typed product schema and mass-balance relationships."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from fresh_tipsy.tables.columns import load_columns


class ProductGroup(StrEnum):
    """Product groups in the TIPSY Full table."""

    LUMBER_2_OR_BETTER = "lumber_2_or_better"
    RESIDUE = "residue"
    LOG_GRADE = "log_grade"
    LUMBER_GRADED = "lumber_graded"
    LUMBER_DEGRADED = "lumber_degraded"
    INDUSTRIAL_LOG = "industrial_log"


@dataclass(frozen=True)
class ProductField:
    """One product or grade column.

    Parameters
    ----------
    name : str
        Source column name.
    group : ProductGroup
        Product group.
    position : int
        Zero-based position in the `.taf` row.
    units : str
        Source unit.
    evidence : str
        Evidence label; always ``model_output``.
    grade : str or None
        Lumber grade, when applicable.
    dimension : str or None
        Lumber dimension, when applicable.
    detail : str or None
        Residue, log-grade, or industrial-log code.
    """

    name: str
    group: ProductGroup
    position: int
    units: str
    evidence: str
    grade: str | None
    dimension: str | None
    detail: str | None


@dataclass(frozen=True)
class ProductTotal:
    """A product aggregate that is not a stored `.taf` column.

    Parameters
    ----------
    name : str
        Aggregate name.
    units : str
        Source unit.
    evidence : str
        Evidence label.
    description : str
        What the aggregate sums.
    """

    name: str
    units: str
    evidence: str
    description: str


@dataclass(frozen=True)
class MassBalanceRule:
    """A product-total reconciliation rule.

    Parameters
    ----------
    name : str
        Rule name.
    total_field : str or None
        Total field, or ``None`` when the source has no total.
    component_fields : tuple of str
        Components that must sum to the total.
    tolerance : float
        Absolute tolerance for the reconciliation.
    note : str
        Human-readable caveat.
    """

    name: str
    total_field: str | None
    component_fields: tuple[str, ...]
    tolerance: float
    note: str


_TAF_COLUMNS = load_columns("taf")
_BY_NAME = {column.name: column for column in _TAF_COLUMNS}
_GRADES: tuple[tuple[str, str], ...] = (
    ("SS", "SS"),
    ("1", "#1"),
    ("2", "#2"),
    ("3", "#3"),
    ("4", "#4"),
)
_DIMENSIONS: tuple[str, ...] = ("2x4", "2x6", "2x8", "2x10")
_INDUSTRIAL_CODES: tuple[str, ...] = (
    "D38L13",
    "D38L11",
    "D38L8",
    "D30L13",
    "D30L11",
    "D30L8",
    "D20L13",
    "D20L11",
    "D20L8",
    "D125L13",
    "D125L11",
    "D125L8",
    "D125L63",
    "D125L51",
    "D125L5",
    "D305",
    "D254",
    "D203",
    "D178",
    "D152",
)


def _field(
    name: str,
    group: ProductGroup,
    *,
    grade: str | None = None,
    dimension: str | None = None,
    detail: str | None = None,
) -> ProductField:
    """Build one product field from the packaged column map.

    Parameters
    ----------
    name : str
        Source column name.
    group : ProductGroup
        Product group.
    grade : str or None, optional
        Lumber grade.
    dimension : str or None, optional
        Lumber dimension.
    detail : str or None, optional
        Residue, log-grade, or industrial-log code.

    Returns
    -------
    ProductField
        Product field.

    Raises
    ------
    KeyError
        When the name is missing from the column map.
    """
    column = _BY_NAME[name]
    return ProductField(
        name=name,
        group=group,
        position=column.position,
        units=column.units,
        evidence="model_output",
        grade=grade,
        dimension=dimension,
        detail=detail,
    )


def _build_fields() -> tuple[ProductField, ...]:
    """Build the 77 typed product fields.

    Returns
    -------
    tuple of ProductField
        All product fields in source order.
    """
    fields: list[ProductField] = []
    for dimension in _DIMENSIONS:
        fields.append(
            _field(
                f"Lumber_2_or_Better_{dimension}",
                ProductGroup.LUMBER_2_OR_BETTER,
                dimension=dimension,
            )
        )
    for detail in ("Chips", "Sawdust", "Shavings", "Trim", "Bark"):
        fields.append(_field(f"Residual_{detail}", ProductGroup.RESIDUE, detail=detail))
    for detail in ("D", "F", "H", "I", "J", "U", "X", "Y"):
        fields.append(_field(f"Logs_Grade_{detail}", ProductGroup.LOG_GRADE, detail=detail))
    for grade, _label in _GRADES:
        for dimension in _DIMENSIONS:
            fields.append(
                _field(
                    f"Lumber_Graded_{grade}_{dimension}",
                    ProductGroup.LUMBER_GRADED,
                    grade=grade,
                    dimension=dimension,
                )
            )
    for grade, _label in _GRADES:
        for dimension in _DIMENSIONS:
            fields.append(
                _field(
                    f"Lumber_Degraded_{grade}_{dimension}",
                    ProductGroup.LUMBER_DEGRADED,
                    grade=grade,
                    dimension=dimension,
                )
            )
    for code in _INDUSTRIAL_CODES:
        fields.append(_field(f"Industrial_Logs_{code}", ProductGroup.INDUSTRIAL_LOG, detail=code))
    return tuple(fields)


PRODUCT_FIELDS: tuple[ProductField, ...] = _build_fields()
PRODUCT_BY_NAME: dict[str, ProductField] = {field.name: field for field in PRODUCT_FIELDS}
PRODUCT_TOTALS: tuple[ProductTotal, ...] = (
    ProductTotal(
        "Lumber_2_or_Better_All",
        "bf/ha",
        "model_output",
        "Sum of the #2 & Better lumber dimensions.",
    ),
    ProductTotal(
        "Lumber_Graded_All",
        "bf/ha",
        "model_output",
        "Sum of the graded lumber dimensions.",
    ),
    ProductTotal(
        "Lumber_Degraded_All",
        "bf/ha",
        "model_output",
        "Sum of the degraded lumber dimensions.",
    ),
    ProductTotal(
        "Logs_Grade_All",
        "m³/ha",
        "model_output",
        "Sum of the log grades.",
    ),
    ProductTotal("LRF_2_or_Better_All", "bf/m³", "model_output", "Lumber recovery factor."),
    ProductTotal("LRF_Graded_All", "bf/m³", "model_output", "Graded lumber recovery factor."),
    ProductTotal("LRF_Degraded_All", "bf/m³", "model_output", "Degraded lumber recovery factor."),
)
MASS_BALANCE_RULES: tuple[MassBalanceRule, ...] = (
    MassBalanceRule(
        "lumber_2_or_better",
        "Lumber_2_or_Better_All",
        tuple(f"Lumber_2_or_Better_{dimension}" for dimension in _DIMENSIONS),
        1e-6,
        "The four #2 & Better dimensions sum to the reported total.",
    ),
    MassBalanceRule(
        "lumber_graded",
        "Lumber_Graded_All",
        tuple(
            f"Lumber_Graded_{grade}_{dimension}"
            for grade, _label in _GRADES
            for dimension in _DIMENSIONS
        ),
        1e-6,
        "Twenty graded dimensions sum to the reported total.",
    ),
    MassBalanceRule(
        "lumber_degraded",
        "Lumber_Degraded_All",
        tuple(
            f"Lumber_Degraded_{grade}_{dimension}"
            for grade, _label in _GRADES
            for dimension in _DIMENSIONS
        ),
        1e-6,
        "Twenty degraded dimensions sum to the reported total.",
    ),
    MassBalanceRule(
        "logs",
        "Logs_Grade_All",
        tuple(f"Logs_Grade_{detail}" for detail in ("D", "F", "H", "I", "J", "U", "X", "Y")),
        1e-6,
        "Eight log grades sum to the reported total.",
    ),
    MassBalanceRule(
        "residues",
        None,
        tuple(f"Residual_{detail}" for detail in ("Chips", "Sawdust", "Shavings", "Trim", "Bark")),
        1e-6,
        "No residue total is stored; components are reported individually.",
    ),
)


def product_field(name: str) -> ProductField:
    """Return one product field by name.

    Parameters
    ----------
    name : str
        Source column name.

    Returns
    -------
    ProductField
        The field.

    Raises
    ------
    KeyError
        When the name is not a product field.
    """
    try:
        return PRODUCT_BY_NAME[name]
    except KeyError as exc:
        message = f"unknown product field: {name}"
        raise KeyError(message) from exc

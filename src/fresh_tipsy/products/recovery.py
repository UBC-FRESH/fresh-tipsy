"""Product recovery and mass-balance checks over TIPSY product columns."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from fresh_tipsy.curves.models import Provenance, QueryResult
from fresh_tipsy.products.errors import MassBalanceError, ProductUnavailableError
from fresh_tipsy.products.schema import (
    MASS_BALANCE_RULES,
    PRODUCT_FIELDS,
    MassBalanceRule,
    ProductField,
    ProductGroup,
)


@dataclass(frozen=True)
class ProductQuantity:
    """One product value.

    Parameters
    ----------
    field : ProductField
        Product field.
    value : float or None
        Source value, or ``None`` when blank.
    """

    field: ProductField
    value: float | None

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-ready product quantity.

        Returns
        -------
        dict of str to object
            Quantity fields.
        """
        return {
            "name": self.field.name,
            "group": self.field.group.value,
            "grade": self.field.grade,
            "dimension": self.field.dimension,
            "detail": self.field.detail,
            "value": self.value,
            "units": self.field.units,
            "evidence": self.field.evidence,
        }


@dataclass(frozen=True)
class ProductTotals:
    """Aggregated product totals.

    Parameters
    ----------
    lumber_2_or_better_bf_ha : float or None
        #2 & Better lumber total.
    graded_bf_ha : float or None
        Graded lumber total.
    degraded_bf_ha : float or None
        Degraded lumber total.
    logs_m3_ha : float or None
        Log-grade total.
    residues_odt_ha : float or None
        Residue component total; no source total exists.
    industrial_m3_ha : float or None
        Industrial-log total.
    """

    lumber_2_or_better_bf_ha: float | None
    graded_bf_ha: float | None
    degraded_bf_ha: float | None
    logs_m3_ha: float | None
    residues_odt_ha: float | None
    industrial_m3_ha: float | None


@dataclass(frozen=True)
class MassBalanceCheck:
    """One product mass-balance result.

    Parameters
    ----------
    name : str
        Check name.
    total_name : str or None
        Total field or aggregate name.
    total_value : float or None
        Total value.
    component_sum : float or None
        Sum of components.
    difference : float or None
        ``total_value - component_sum``.
    tolerance : float
        Absolute tolerance.
    status : str
        ``"pass"``, ``"fail"``, or ``"unavailable"``.
    independent : bool
        Whether the check compares independent source fields.
    note : str
        Human-readable caveat.
    """

    name: str
    total_name: str | None
    total_value: float | None
    component_sum: float | None
    difference: float | None
    tolerance: float
    status: str
    independent: bool
    note: str

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-ready check.

        Returns
        -------
        dict of str to object
            Check fields.
        """
        return {
            "name": self.name,
            "total_name": self.total_name,
            "total_value": self.total_value,
            "component_sum": self.component_sum,
            "difference": self.difference,
            "tolerance": self.tolerance,
            "status": self.status,
            "independent": self.independent,
            "note": self.note,
        }


@dataclass(frozen=True)
class ProductRecovery:
    """Recovered product groups, totals, and mass-balance checks.

    Parameters
    ----------
    age : float
        Query age.
    scenario : str
        Scenario label.
    provenance : Provenance
        Source provenance.
    lumber_2_or_better : tuple of ProductQuantity
        #2 & Better lumber dimensions.
    residues : tuple of ProductQuantity
        Mill residue components.
    log_grades : tuple of ProductQuantity
        Log grades.
    graded_lumber : tuple of ProductQuantity
        Graded lumber dimensions.
    degraded_lumber : tuple of ProductQuantity
        Degraded lumber dimensions.
    industrial_logs : tuple of ProductQuantity
        Industrial-log codes.
    totals : ProductTotals
        Aggregated totals.
    checks : tuple of MassBalanceCheck
        Mass-balance checks.
    """

    age: float
    scenario: str
    provenance: Provenance
    lumber_2_or_better: tuple[ProductQuantity, ...]
    residues: tuple[ProductQuantity, ...]
    log_grades: tuple[ProductQuantity, ...]
    graded_lumber: tuple[ProductQuantity, ...]
    degraded_lumber: tuple[ProductQuantity, ...]
    industrial_logs: tuple[ProductQuantity, ...]
    totals: ProductTotals
    checks: tuple[MassBalanceCheck, ...]

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-ready product recovery.

        Returns
        -------
        dict of str to object
            Recovery fields.
        """
        return {
            "age": self.age,
            "scenario": self.scenario,
            "provenance": self.provenance.as_dict(),
            "lumber_2_or_better": [item.as_dict() for item in self.lumber_2_or_better],
            "residues": [item.as_dict() for item in self.residues],
            "log_grades": [item.as_dict() for item in self.log_grades],
            "graded_lumber": [item.as_dict() for item in self.graded_lumber],
            "degraded_lumber": [item.as_dict() for item in self.degraded_lumber],
            "industrial_logs": [item.as_dict() for item in self.industrial_logs],
            "totals": {
                "lumber_2_or_better_bf_ha": self.totals.lumber_2_or_better_bf_ha,
                "graded_bf_ha": self.totals.graded_bf_ha,
                "degraded_bf_ha": self.totals.degraded_bf_ha,
                "logs_m3_ha": self.totals.logs_m3_ha,
                "residues_odt_ha": self.totals.residues_odt_ha,
                "industrial_m3_ha": self.totals.industrial_m3_ha,
            },
            "checks": [check.as_dict() for check in self.checks],
        }


def _sum_values(quantities: Sequence[ProductQuantity]) -> float | None:
    """Sum available values in a product group.

    Parameters
    ----------
    quantities : sequence of ProductQuantity
        Product quantities.

    Returns
    -------
    float or None
        Sum, or ``None`` when every value is blank.
    """
    available = [item.value for item in quantities if item.value is not None]
    if not available:
        return None
    return sum(available)


def _check(
    name: str,
    total_name: str | None,
    total_value: float | None,
    component_sum: float | None,
    tolerance: float,
    *,
    independent: bool,
    note: str,
) -> MassBalanceCheck:
    """Build one mass-balance check.

    Parameters
    ----------
    name : str
        Check name.
    total_name : str or None
        Total field or aggregate.
    total_value : float or None
        Total value.
    component_sum : float or None
        Component sum.
    tolerance : float
        Absolute tolerance.
    independent : bool
        Whether the check uses independent source fields.
    note : str
        Human-readable caveat.

    Returns
    -------
    MassBalanceCheck
        Check result.
    """
    if total_value is None or component_sum is None:
        status = "unavailable"
        difference = None
    else:
        difference = total_value - component_sum
        status = "pass" if abs(difference) <= tolerance else "fail"
    return MassBalanceCheck(
        name=name,
        total_name=total_name,
        total_value=total_value,
        component_sum=component_sum,
        difference=difference,
        tolerance=tolerance,
        status=status,
        independent=independent,
        note=note,
    )


def _rule_check(rule: MassBalanceRule, quantities: Sequence[ProductQuantity]) -> MassBalanceCheck:
    """Evaluate one schema mass-balance rule.

    Parameters
    ----------
    rule : MassBalanceRule
        Rule.
    quantities : sequence of ProductQuantity
        Product quantities.

    Returns
    -------
    MassBalanceCheck
        Check result.
    """
    components = [item for item in quantities if item.field.name in rule.component_fields]
    component_sum = _sum_values(components)
    if rule.total_field is None:
        return _check(
            rule.name,
            None,
            None,
            component_sum,
            rule.tolerance,
            independent=False,
            note=rule.note,
        )
    total_value = component_sum
    return _check(
        rule.name,
        rule.total_field,
        total_value,
        component_sum,
        rule.tolerance,
        independent=False,
        note=f"{rule.note} No stored total; the aggregate is derived from the components.",
    )


def recover_products(result: QueryResult, *, strict: bool = True) -> ProductRecovery:
    """Recover product groups and run mass-balance checks.

    Parameters
    ----------
    result : QueryResult
        Query result from a `.taf` table.
    strict : bool, optional
        Raise when a mass-balance check fails. Defaults to ``True``.

    Returns
    -------
    ProductRecovery
        Recovered groups, totals, and checks.

    Raises
    ------
    ProductUnavailableError
        When the selected table is not a `.taf` table.
    MassBalanceError
        When ``strict`` is true and a check fails.
    """
    if result.selection.entry.format != "taf":
        message = "product recovery requires a .taf table"
        raise ProductUnavailableError(message)
    values = result.row.values
    quantities = tuple(
        ProductQuantity(
            field=field,
            value=values[field.position - 1] if field.position - 1 < len(values) else None,
        )
        for field in PRODUCT_FIELDS
    )
    groups = {
        group: tuple(item for item in quantities if item.field.group is group)
        for group in ProductGroup
    }
    totals = ProductTotals(
        lumber_2_or_better_bf_ha=_sum_values(groups[ProductGroup.LUMBER_2_OR_BETTER]),
        graded_bf_ha=_sum_values(groups[ProductGroup.LUMBER_GRADED]),
        degraded_bf_ha=_sum_values(groups[ProductGroup.LUMBER_DEGRADED]),
        logs_m3_ha=_sum_values(groups[ProductGroup.LOG_GRADE]),
        residues_odt_ha=_sum_values(groups[ProductGroup.RESIDUE]),
        industrial_m3_ha=_sum_values(groups[ProductGroup.INDUSTRIAL_LOG]),
    )
    checks = [_rule_check(rule, quantities) for rule in MASS_BALANCE_RULES]
    lumber_2_or_better = groups[ProductGroup.LUMBER_2_OR_BETTER]
    graded = groups[ProductGroup.LUMBER_GRADED]
    graded_better = tuple(item for item in graded if item.field.grade in {"SS", "1", "2"})
    total_2_or_better = _sum_values(lumber_2_or_better)
    better_sum = _sum_values(graded_better)
    all_graded_sum = _sum_values(graded)
    if total_2_or_better is None or (better_sum is None and all_graded_sum is None):
        cross_status = "unavailable"
        cross_sum = better_sum
        cross_note = "#2 & Better or graded components are blank at this age."
    elif better_sum is not None and abs(total_2_or_better - better_sum) <= 1e-6:
        cross_status = "pass"
        cross_sum = better_sum
        cross_note = "#2 & Better equals graded SS, #1, and #2 dimensions."
    elif all_graded_sum is not None and abs(total_2_or_better - all_graded_sum) <= 1e-6:
        cross_status = "pass"
        cross_sum = all_graded_sum
        cross_note = (
            "Some tables (observed in `dr`) report all graded grades in the "
            "#2 & Better aggregate; this reconciliation uses all five grades."
        )
    else:
        cross_status = "fail"
        cross_sum = better_sum if better_sum is not None else all_graded_sum
        cross_note = "#2 & Better does not reconcile with the graded breakdown."
    checks.append(
        MassBalanceCheck(
            name="lumber_2_or_better_vs_graded",
            total_name="Lumber_2_or_Better_All",
            total_value=total_2_or_better,
            component_sum=cross_sum,
            difference=(
                None
                if total_2_or_better is None or cross_sum is None
                else total_2_or_better - cross_sum
            ),
            tolerance=1e-6,
            status=cross_status,
            independent=True,
            note=cross_note,
        )
    )
    failed = [check for check in checks if check.status == "fail"]
    if strict and failed:
        names = ", ".join(check.name for check in failed)
        message = f"product mass balance failed: {names}"
        raise MassBalanceError(message)
    return ProductRecovery(
        age=result.row.age,
        scenario=result.row.scenario,
        provenance=result.selection.provenance,
        lumber_2_or_better=lumber_2_or_better,
        residues=groups[ProductGroup.RESIDUE],
        log_grades=groups[ProductGroup.LOG_GRADE],
        graded_lumber=graded,
        degraded_lumber=groups[ProductGroup.LUMBER_DEGRADED],
        industrial_logs=groups[ProductGroup.INDUSTRIAL_LOG],
        totals=totals,
        checks=tuple(checks),
    )

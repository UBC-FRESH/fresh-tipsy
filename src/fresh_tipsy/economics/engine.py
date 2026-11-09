"""Reimplemented product revenue, NPV, site value, and sensitivity."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from math import pow as math_pow

from fresh_tipsy.economics.errors import (
    AmbiguousPriceError,
    InvalidEconomicsInputError,
    MissingPriceError,
    UnitMismatchError,
)
from fresh_tipsy.economics.models import (
    CashFlow,
    CostCategory,
    CostLine,
    DiscountAssumptions,
    EconomicGap,
    EconomicResult,
    EconomicsRequest,
    PriceKey,
    RevenueLine,
    SensitivityCase,
    SensitivityCaseResult,
    SensitivityResult,
)
from fresh_tipsy.products import ProductGroup, ProductQuantity, ProductRecovery

_GROUP_ITEMS: dict[ProductGroup, Callable[[ProductRecovery], tuple[ProductQuantity, ...]]] = {
    ProductGroup.LUMBER_2_OR_BETTER: lambda recovery: recovery.lumber_2_or_better,
    ProductGroup.RESIDUE: lambda recovery: recovery.residues,
    ProductGroup.LOG_GRADE: lambda recovery: recovery.log_grades,
    ProductGroup.LUMBER_GRADED: lambda recovery: recovery.graded_lumber,
    ProductGroup.LUMBER_DEGRADED: lambda recovery: recovery.degraded_lumber,
    ProductGroup.INDUSTRIAL_LOG: lambda recovery: recovery.industrial_logs,
}

_UNIT_FACTORS: dict[str, tuple[float, str]] = {
    "bf": (1.0, "board_foot"),
    "mbf": (1000.0, "board_foot"),
    "m3": (1.0, "volume"),
    "odt": (1.0, "oven_dry_tonne"),
}


def _normalize_unit(unit: str) -> str:
    """Normalize a unit token.

    Parameters
    ----------
    unit : str
        Unit token.

    Returns
    -------
    str
        Lowercase token with superscript digits expanded.
    """
    return unit.strip().lower().replace("³", "3").replace("²", "2")


def _unit_factor(price_unit: str, quantity_unit: str) -> float:
    """Return the factor that converts a price to a quantity unit.

    Parameters
    ----------
    price_unit : str
        Price unit, such as ``"CAD/mbf"``.
    quantity_unit : str
        Quantity unit, such as ``"bf/ha"``.

    Returns
    -------
    float
        Multiplier applied to ``quantity * price``.

    Raises
    ------
    UnitMismatchError
        When the units are not compatible.
    """
    price_parts = price_unit.split("/")
    quantity_parts = quantity_unit.split("/")
    if len(price_parts) != 2 or price_parts[0].strip().upper() != "CAD":
        message = f"price unit must be CAD/<unit>: {price_unit!r}"
        raise UnitMismatchError(message)
    if len(quantity_parts) != 2 or _normalize_unit(quantity_parts[1]) != "ha":
        message = f"quantity unit must be <unit>/ha: {quantity_unit!r}"
        raise UnitMismatchError(message)
    price_token = _normalize_unit(price_parts[1])
    quantity_token = _normalize_unit(quantity_parts[0])
    if price_token not in _UNIT_FACTORS or quantity_token not in _UNIT_FACTORS:
        message = f"unsupported price/quantity units: {price_unit!r}, {quantity_unit!r}"
        raise UnitMismatchError(message)
    price_factor, price_dimension = _UNIT_FACTORS[price_token]
    quantity_factor, quantity_dimension = _UNIT_FACTORS[quantity_token]
    if price_dimension != quantity_dimension:
        message = f"price unit {price_unit!r} cannot price quantity unit {quantity_unit!r}"
        raise UnitMismatchError(message)
    return quantity_factor / price_factor


def _escalation_factor(age: float, rate: float, duration: float) -> float:
    """Return a real escalation factor.

    Parameters
    ----------
    age : float
        Years since disturbance.
    rate : float
        Annual real increase.
    duration : float
        Maximum years of compounding.

    Returns
    -------
    float
        Escalation factor.
    """
    if duration <= 0:
        return 1.0
    return math_pow(1.0 + rate, min(age, duration))


def _discount_factor(
    age: float,
    rate: float,
    base_age: float,
    include_sunk_costs: bool,
) -> float | None:
    """Return a discount factor to the base age.

    Parameters
    ----------
    age : float
        Years since disturbance.
    rate : float
        Discount rate.
    base_age : float
        Base age.
    include_sunk_costs : bool
        Include flows before the base age.

    Returns
    -------
    float or None
        Present-value multiplier, or ``None`` when a pre-base flow is excluded.
    """
    if age < base_age and not include_sunk_costs:
        return None
    return math_pow(1.0 + rate, base_age - age)


def _direction(base: float | None, case: float | None) -> str:
    """Return the direction of an NPV change.

    Parameters
    ----------
    base : float or None
        Base NPV.
    case : float or None
        Case NPV.

    Returns
    -------
    str
        ``"increase"``, ``"decrease"``, ``"unchanged"``, or ``"unavailable"``.
    """
    if base is None or case is None:
        return "unavailable"
    difference = case - base
    if difference > 1e-9:
        return "increase"
    if difference < -1e-9:
        return "decrease"
    return "unchanged"


def evaluate_economics(request: EconomicsRequest) -> EconomicResult:
    """Evaluate product revenue, costs, NPV, and site value.

    Parameters
    ----------
    request : EconomicsRequest
        Product recovery, prices, costs, and discount assumptions.

    Returns
    -------
    EconomicResult
        Reimplemented result with explicit gaps.
    """
    return _evaluate(
        request,
        request.assumptions,
        price_multiplier=1.0,
        cost_multiplier=1.0,
        cost_categories=(),
    )


def _evaluate(
    request: EconomicsRequest,
    assumptions: DiscountAssumptions,
    *,
    price_multiplier: float,
    cost_multiplier: float,
    cost_categories: tuple[CostCategory, ...],
) -> EconomicResult:
    """Evaluate with internal sensitivity multipliers."""
    recovery = request.recovery
    revenue_lines: list[RevenueLine] = []
    gaps: list[EconomicGap] = []
    price_sources: set[str] = set()
    total_revenue = 0.0
    for group in request.revenue_groups:
        accessor = _GROUP_ITEMS[group]
        for item in accessor(recovery):
            if item.value is None or item.value == 0:
                continue
            key = PriceKey(
                species_code=recovery.species_code,
                group=group,
                period=request.period,
                grade=item.field.grade,
                dimension=item.field.dimension,
                detail=item.field.detail,
            )
            try:
                price = request.price_book.lookup(key)
            except MissingPriceError as exc:
                gaps.append(EconomicGap("missing_price", str(exc), product=item.field.name))
                continue
            except AmbiguousPriceError as exc:
                gaps.append(EconomicGap("ambiguous_price", str(exc), product=item.field.name))
                continue
            try:
                unit_factor = _unit_factor(price.unit, item.field.units)
            except UnitMismatchError as exc:
                gaps.append(EconomicGap("unit_mismatch", str(exc), product=item.field.name))
                continue
            revenue = item.value * price.price_per_unit * unit_factor * price_multiplier
            total_revenue += revenue
            price_sources.add(price.source)
            revenue_lines.append(
                RevenueLine(
                    product_name=item.field.name,
                    group=group,
                    quantity=item.value,
                    quantity_units=item.field.units,
                    price_per_unit=price.price_per_unit,
                    price_units=price.unit,
                    unit_factor=unit_factor,
                    revenue_per_ha=revenue,
                    source=price.source,
                    citation=price.citation,
                )
            )
    result_revenue: float | None = None if gaps else total_revenue

    cost_lines: list[CostLine] = []
    cost_sources: set[str] = set()
    total_cost = 0.0
    selected_categories = set(cost_categories)
    for entry in sorted(request.costs, key=lambda cost: (cost.age, cost.label)):
        multiplier = (
            cost_multiplier
            if not selected_categories or entry.category in selected_categories
            else 1.0
        )
        amount = entry.amount_per_ha * multiplier
        total_cost += amount
        cost_sources.add(entry.source)
        cost_lines.append(
            CostLine(
                category=entry.category,
                age=entry.age,
                amount_per_ha=amount,
                label=entry.label,
                source=entry.source,
                citation=entry.citation,
            )
        )

    cash_flows: list[CashFlow] = []
    discounted_revenue: float | None = 0.0 if result_revenue is not None else None
    if result_revenue is not None:
        discount_factor = _discount_factor(
            recovery.age,
            assumptions.discount_rate,
            assumptions.base_age,
            assumptions.include_sunk_costs,
        )
        if discount_factor is None:
            discounted_revenue = 0.0
        else:
            escalated = result_revenue * _escalation_factor(
                recovery.age,
                assumptions.real_price_increase,
                assumptions.real_increase_duration,
            )
            discounted_revenue = escalated * discount_factor
            cash_flows.append(
                CashFlow(
                    age=recovery.age,
                    kind="revenue",
                    label="product revenue",
                    amount_per_ha=result_revenue,
                    escalated_per_ha=escalated,
                    discounted_per_ha=discounted_revenue,
                )
            )
    discounted_cost = 0.0
    for line in cost_lines:
        discount_factor = _discount_factor(
            line.age,
            assumptions.discount_rate,
            assumptions.base_age,
            assumptions.include_sunk_costs,
        )
        if discount_factor is None:
            continue
        escalated = line.amount_per_ha * _escalation_factor(
            line.age,
            assumptions.real_cost_increase,
            assumptions.real_increase_duration,
        )
        discounted = escalated * discount_factor
        discounted_cost += discounted
        cash_flows.append(
            CashFlow(
                age=line.age,
                kind="cost",
                label=line.label,
                amount_per_ha=line.amount_per_ha,
                escalated_per_ha=escalated,
                discounted_per_ha=discounted,
            )
        )
    npv: float | None = None
    if discounted_revenue is not None:
        npv = discounted_revenue - discounted_cost
    benefit_cost_ratio: float | None = None
    if discounted_revenue is not None and discounted_cost > 0:
        benefit_cost_ratio = discounted_revenue / discounted_cost
    site_value: float | None = None
    if npv is not None:
        if assumptions.discount_rate <= 0 or recovery.age <= 0:
            gaps.append(
                EconomicGap(
                    "site_value_unavailable",
                    "site value requires a positive discount rate and harvest age",
                )
            )
        else:
            growth = (1.0 + assumptions.discount_rate) ** recovery.age
            site_value = npv * growth / (growth - 1.0)
    return EconomicResult(
        species_code=recovery.species_code,
        age=recovery.age,
        period=request.period,
        source_model=recovery.provenance.source_model,
        source_version=recovery.provenance.source_version,
        source_relative_path=recovery.provenance.relative_path,
        source_sha256=recovery.provenance.sha256,
        source_citation=recovery.provenance.citation,
        price_sources=tuple(sorted(price_sources)),
        cost_sources=tuple(sorted(cost_sources)),
        assumptions=assumptions,
        revenue_per_ha=result_revenue,
        cost_per_ha=total_cost,
        discounted_revenue_per_ha=discounted_revenue,
        discounted_cost_per_ha=discounted_cost,
        npv_per_ha=npv,
        site_value_per_ha=site_value,
        benefit_cost_ratio=benefit_cost_ratio,
        revenue_lines=tuple(revenue_lines),
        cost_lines=tuple(cost_lines),
        cash_flows=tuple(sorted(cash_flows, key=lambda flow: (flow.age, flow.kind))),
        gaps=tuple(gaps),
    )


def evaluate_sensitivity(
    request: EconomicsRequest,
    cases: tuple[SensitivityCase, ...],
) -> SensitivityResult:
    """Evaluate a base result and sensitivity cases.

    Parameters
    ----------
    request : EconomicsRequest
        Base request.
    cases : tuple of SensitivityCase
        Sensitivity cases.

    Returns
    -------
    SensitivityResult
        Base and evaluated cases.

    Raises
    ------
    InvalidEconomicsInputError
        When a case produces a negative discount rate.
    """
    base = evaluate_economics(request)
    results: list[SensitivityCaseResult] = []
    for case in cases:
        rate = request.assumptions.discount_rate + case.discount_rate_delta
        if rate < 0:
            message = f"case {case.name!r} produces a negative discount rate"
            raise InvalidEconomicsInputError(message)
        assumptions = replace(request.assumptions, discount_rate=rate)
        result = _evaluate(
            request,
            assumptions,
            price_multiplier=case.price_multiplier,
            cost_multiplier=case.cost_multiplier,
            cost_categories=case.cost_categories,
        )
        change = None
        if base.npv_per_ha is not None and result.npv_per_ha is not None:
            change = result.npv_per_ha - base.npv_per_ha
        results.append(
            SensitivityCaseResult(
                case=case,
                result=result,
                npv_change_per_ha=change,
                direction=_direction(base.npv_per_ha, result.npv_per_ha),
            )
        )
    return SensitivityResult(base=base, cases=tuple(results))

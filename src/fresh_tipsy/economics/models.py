"""Typed economic inputs, outputs, and sensitivity cases."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite

from fresh_tipsy.economics.errors import (
    AmbiguousPriceError,
    InvalidEconomicsInputError,
    MissingPriceError,
)
from fresh_tipsy.products import ProductGroup, ProductRecovery

_DEFAULT_DISCOUNT_CITATION = (
    "FAN$IER Help, Discount Assumptions: 4% default discount rate, 0% real "
    "price and cost increase, 25-year real increase duration, base age zero."
)


class CostCategory(StrEnum):
    """Cost categories aligned with the FAN$IER cost sections."""

    REGENERATION = "regeneration"
    POST_REGENERATION = "post_regeneration"
    HARVEST = "harvest"
    COMMERCIAL_THIN = "commercial_thin"
    TRANSPORT = "transport"
    MILLING = "milling"
    ROADS = "roads"
    ANNUAL = "annual"
    OTHER = "other"


def _text(value: str, name: str) -> None:
    """Validate a required text field.

    Parameters
    ----------
    value : str
        Field value.
    name : str
        Field name.

    Raises
    ------
    InvalidEconomicsInputError
        When the value is empty.
    """
    if not value.strip():
        message = f"{name} must not be empty"
        raise InvalidEconomicsInputError(message)


def _finite(value: float, name: str) -> None:
    """Validate a finite number.

    Parameters
    ----------
    value : float
        Field value.
    name : str
        Field name.

    Raises
    ------
    InvalidEconomicsInputError
        When the value is not finite.
    """
    if not isfinite(value):
        message = f"{name} must be finite"
        raise InvalidEconomicsInputError(message)


@dataclass(frozen=True)
class PriceKey:
    """A price lookup key.

    Parameters
    ----------
    species_code : str
        Species code, case-insensitive.
    group : ProductGroup
        Product group.
    period : str, optional
        Price period label. Defaults to ``"default"``.
    grade : str or None, optional
        Lumber grade, when applicable.
    dimension : str or None, optional
        Lumber dimension, when applicable.
    detail : str or None, optional
        Residue, log-grade, or industrial-log code.
    """

    species_code: str
    group: ProductGroup
    period: str = "default"
    grade: str | None = None
    dimension: str | None = None
    detail: str | None = None

    def __post_init__(self) -> None:
        """Validate the lookup key.

        Raises
        ------
        InvalidEconomicsInputError
            When a required field is empty.
        """
        _text(self.species_code, "species_code")
        _text(self.period, "period")
        for name, value in (
            ("grade", self.grade),
            ("dimension", self.dimension),
            ("detail", self.detail),
        ):
            if value is not None:
                _text(value, name)

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-ready key.

        Returns
        -------
        dict of str to object
            Key fields.
        """
        return {
            "species_code": self.species_code,
            "group": self.group.value,
            "period": self.period,
            "grade": self.grade,
            "dimension": self.dimension,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class PriceEntry:
    """One explicit product price.

    Parameters
    ----------
    key : PriceKey
        Lookup key. A ``None`` grade, dimension, or detail is a wildcard.
    price_per_unit : float
        Price in the stated unit.
    unit : str
        Currency and denominator, such as ``"CAD/mbf"`` or ``"CAD/m³"``.
    source : str
        Source label for the assumption.
    citation : str
        Citation or note describing the source.
    evidence : str, optional
        Input label. Defaults to ``"assumption"``.
    """

    key: PriceKey
    price_per_unit: float
    unit: str
    source: str
    citation: str
    evidence: str = "assumption"

    def __post_init__(self) -> None:
        """Validate the price entry.

        Raises
        ------
        InvalidEconomicsInputError
            When a value is malformed.
        """
        _finite(self.price_per_unit, "price_per_unit")
        if self.price_per_unit < 0:
            message = "price_per_unit must be non-negative"
            raise InvalidEconomicsInputError(message)
        _text(self.unit, "unit")
        _text(self.source, "source")
        _text(self.citation, "citation")
        _text(self.evidence, "evidence")

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-ready price entry.

        Returns
        -------
        dict of str to object
            Price fields.
        """
        return {
            "key": self.key.as_dict(),
            "price_per_unit": self.price_per_unit,
            "unit": self.unit,
            "source": self.source,
            "citation": self.citation,
            "evidence": self.evidence,
        }


@dataclass(frozen=True)
class PriceBook:
    """A collection of explicit prices.

    Parameters
    ----------
    entries : tuple of PriceEntry, optional
        Price entries.
    """

    entries: tuple[PriceEntry, ...] = ()

    def lookup(self, key: PriceKey) -> PriceEntry:
        """Return the most specific price for a key.

        Parameters
        ----------
        key : PriceKey
            Requested product.

        Returns
        -------
        PriceEntry
            Matching price.

        Raises
        ------
        MissingPriceError
            When no price matches.
        AmbiguousPriceError
            When multiple prices are equally specific.
        """
        matches = [
            entry
            for entry in self.entries
            if entry.key.species_code.casefold() == key.species_code.casefold()
            and entry.key.group is key.group
            and entry.key.period == key.period
            and (entry.key.grade is None or entry.key.grade == key.grade)
            and (entry.key.dimension is None or entry.key.dimension == key.dimension)
            and (entry.key.detail is None or entry.key.detail == key.detail)
        ]
        if not matches:
            message = f"no price for {key.species_code} {key.group.value} period {key.period!r}"
            raise MissingPriceError(message)
        specificity = [
            sum(
                value is not None
                for value in (
                    entry.key.grade,
                    entry.key.dimension,
                    entry.key.detail,
                )
            )
            for entry in matches
        ]
        best = max(specificity)
        winners = [
            entry for entry, score in zip(matches, specificity, strict=True) if score == best
        ]
        if len(winners) > 1:
            message = f"ambiguous price for {key.species_code} {key.group.value}"
            raise AmbiguousPriceError(message)
        return winners[0]

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-ready price book.

        Returns
        -------
        dict of str to object
            Price book fields.
        """
        return {"entries": [entry.as_dict() for entry in self.entries]}


@dataclass(frozen=True)
class CostEntry:
    """One explicit per-hectare cost.

    Parameters
    ----------
    category : CostCategory
        Cost category.
    age : float
        Years since disturbance at which the cost occurs.
    amount_per_ha : float
        Cost in CAD per hectare.
    label : str
        Human-readable activity label.
    source : str
        Source label for the assumption.
    citation : str
        Citation or note describing the source.
    evidence : str, optional
        Input label. Defaults to ``"assumption"``.
    """

    category: CostCategory
    age: float
    amount_per_ha: float
    label: str
    source: str
    citation: str
    evidence: str = "assumption"

    def __post_init__(self) -> None:
        """Validate the cost entry.

        Raises
        ------
        InvalidEconomicsInputError
            When a value is malformed.
        """
        _finite(self.age, "age")
        _finite(self.amount_per_ha, "amount_per_ha")
        if self.age < 0:
            message = "age must be non-negative"
            raise InvalidEconomicsInputError(message)
        if self.amount_per_ha < 0:
            message = "amount_per_ha must be non-negative"
            raise InvalidEconomicsInputError(message)
        _text(self.label, "label")
        _text(self.source, "source")
        _text(self.citation, "citation")
        _text(self.evidence, "evidence")

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-ready cost entry.

        Returns
        -------
        dict of str to object
            Cost fields.
        """
        return {
            "category": self.category.value,
            "age": self.age,
            "amount_per_ha": self.amount_per_ha,
            "label": self.label,
            "source": self.source,
            "citation": self.citation,
            "evidence": self.evidence,
        }


@dataclass(frozen=True)
class DiscountAssumptions:
    """Explicit discounting and real-escalation assumptions.

    Parameters
    ----------
    discount_rate : float
        Real annual discount rate as a fraction.
    real_price_increase : float, optional
        Annual real price increase as a fraction. Defaults to 0.
    real_cost_increase : float, optional
        Annual real cost increase as a fraction. Defaults to 0.
    real_increase_duration : float, optional
        Years over which real increases compound. Defaults to 25.
    base_age : float, optional
        Age to which values are discounted. Defaults to 0.
    include_sunk_costs : bool, optional
        Include costs and benefits before ``base_age``. Defaults to false.
    citation : str, optional
        Citation for the assumptions.
    """

    discount_rate: float
    real_price_increase: float = 0.0
    real_cost_increase: float = 0.0
    real_increase_duration: float = 25.0
    base_age: float = 0.0
    include_sunk_costs: bool = False
    citation: str = _DEFAULT_DISCOUNT_CITATION

    def __post_init__(self) -> None:
        """Validate the assumptions.

        Raises
        ------
        InvalidEconomicsInputError
            When a value is malformed or out of range.
        """
        for name, value in (
            ("discount_rate", self.discount_rate),
            ("real_price_increase", self.real_price_increase),
            ("real_cost_increase", self.real_cost_increase),
            ("real_increase_duration", self.real_increase_duration),
            ("base_age", self.base_age),
        ):
            _finite(value, name)
        if self.discount_rate < 0:
            message = "discount_rate must be non-negative"
            raise InvalidEconomicsInputError(message)
        for name, value in (
            ("real_price_increase", self.real_price_increase),
            ("real_cost_increase", self.real_cost_increase),
        ):
            if value <= -1:
                message = f"{name} must be greater than -1"
                raise InvalidEconomicsInputError(message)
        if self.real_increase_duration < 0:
            message = "real_increase_duration must be non-negative"
            raise InvalidEconomicsInputError(message)
        if self.base_age < 0:
            message = "base_age must be non-negative"
            raise InvalidEconomicsInputError(message)
        _text(self.citation, "citation")

    @classmethod
    def fansier_defaults(cls) -> DiscountAssumptions:
        """Return the cited FAN$IER default discount assumptions.

        Returns
        -------
        DiscountAssumptions
            Four percent discount rate with zero real escalation.
        """
        return cls(discount_rate=0.04)

    def as_dict(self) -> dict[str, object]:
        """Return JSON-ready assumptions.

        Returns
        -------
        dict of str to object
            Assumption fields.
        """
        return {
            "discount_rate": self.discount_rate,
            "real_price_increase": self.real_price_increase,
            "real_cost_increase": self.real_cost_increase,
            "real_increase_duration": self.real_increase_duration,
            "base_age": self.base_age,
            "include_sunk_costs": self.include_sunk_costs,
            "citation": self.citation,
        }


@dataclass(frozen=True)
class EconomicsRequest:
    """A product recovery, prices, costs, and discount assumptions.

    Parameters
    ----------
    recovery : ProductRecovery
        Product recovery at the harvest age.
    price_book : PriceBook
        Explicit prices.
    assumptions : DiscountAssumptions
        Discounting assumptions.
    revenue_groups : tuple of ProductGroup
        Product groups that contribute revenue. Select one lumber basis to
        avoid double counting the alternative graded and degraded suites.
    costs : tuple of CostEntry, optional
        Explicit per-hectare costs.
    period : str, optional
        Price period. Defaults to ``"default"``.
    """

    recovery: ProductRecovery
    price_book: PriceBook
    assumptions: DiscountAssumptions
    revenue_groups: tuple[ProductGroup, ...]
    costs: tuple[CostEntry, ...] = ()
    period: str = "default"

    def __post_init__(self) -> None:
        """Validate the request.

        Raises
        ------
        InvalidEconomicsInputError
            When the period is empty or more than one lumber basis is selected.
        """
        _text(self.period, "period")
        if len(set(self.revenue_groups)) != len(self.revenue_groups):
            message = "revenue_groups must not contain duplicates"
            raise InvalidEconomicsInputError(message)
        lumber_groups = {
            ProductGroup.LUMBER_2_OR_BETTER,
            ProductGroup.LUMBER_GRADED,
            ProductGroup.LUMBER_DEGRADED,
        }
        selected_lumber = lumber_groups.intersection(self.revenue_groups)
        if len(selected_lumber) > 1:
            message = (
                "select at most one lumber basis: #2 & Better, graded, or "
                "degraded, to avoid double counting"
            )
            raise InvalidEconomicsInputError(message)


@dataclass(frozen=True)
class RevenueLine:
    """One priced product line.

    Parameters
    ----------
    product_name : str
        Source product field.
    group : ProductGroup
        Product group.
    quantity : float
        Product quantity per hectare.
    quantity_units : str
        Quantity units.
    price_per_unit : float
        Applied price.
    price_units : str
        Price units.
    unit_factor : float
        Conversion from price units to quantity units.
    revenue_per_ha : float
        Revenue in CAD per hectare.
    source : str
        Price source.
    citation : str
        Price citation.
    """

    product_name: str
    group: ProductGroup
    quantity: float
    quantity_units: str
    price_per_unit: float
    price_units: str
    unit_factor: float
    revenue_per_ha: float
    source: str
    citation: str

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-ready revenue line.

        Returns
        -------
        dict of str to object
            Revenue fields.
        """
        return {
            "product_name": self.product_name,
            "group": self.group.value,
            "quantity": self.quantity,
            "quantity_units": self.quantity_units,
            "price_per_unit": self.price_per_unit,
            "price_units": self.price_units,
            "unit_factor": self.unit_factor,
            "revenue_per_ha": self.revenue_per_ha,
            "source": self.source,
            "citation": self.citation,
        }


@dataclass(frozen=True)
class CostLine:
    """One explicit cost line after any sensitivity multiplier.

    Parameters
    ----------
    category : CostCategory
        Cost category.
    age : float
        Years since disturbance.
    amount_per_ha : float
        Effective cost in CAD per hectare.
    label : str
        Activity label.
    source : str
        Cost source.
    citation : str
        Cost citation.
    """

    category: CostCategory
    age: float
    amount_per_ha: float
    label: str
    source: str
    citation: str

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-ready cost line.

        Returns
        -------
        dict of str to object
            Cost fields.
        """
        return {
            "category": self.category.value,
            "age": self.age,
            "amount_per_ha": self.amount_per_ha,
            "label": self.label,
            "source": self.source,
            "citation": self.citation,
        }


@dataclass(frozen=True)
class CashFlow:
    """One escalated and discounted cash flow.

    Parameters
    ----------
    age : float
        Years since disturbance.
    kind : str
        ``"revenue"`` or ``"cost"``.
    label : str
        Cash-flow label.
    amount_per_ha : float
        Unescalated amount in CAD per hectare.
    escalated_per_ha : float
        Amount after real escalation.
    discounted_per_ha : float
        Amount after escalation and discounting.
    """

    age: float
    kind: str
    label: str
    amount_per_ha: float
    escalated_per_ha: float
    discounted_per_ha: float

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-ready cash flow.

        Returns
        -------
        dict of str to object
            Cash-flow fields.
        """
        return {
            "age": self.age,
            "kind": self.kind,
            "label": self.label,
            "amount_per_ha": self.amount_per_ha,
            "escalated_per_ha": self.escalated_per_ha,
            "discounted_per_ha": self.discounted_per_ha,
        }


@dataclass(frozen=True)
class EconomicGap:
    """An explicit missing or incompatible economic input.

    Parameters
    ----------
    code : str
        Stable gap code.
    message : str
        Human-readable explanation.
    product : str or None, optional
        Product field or context.
    """

    code: str
    message: str
    product: str | None = None

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-ready gap.

        Returns
        -------
        dict of str to object
            Gap fields.
        """
        return {"code": self.code, "message": self.message, "product": self.product}


@dataclass(frozen=True)
class EconomicResult:
    """A reimplemented economic result for one harvest age.

    Parameters
    ----------
    species_code : str
        Species code.
    age : float
        Harvest age.
    period : str
        Price period.
    source_model : str
        Growth model name.
    source_version : str
        Growth model version.
    source_relative_path : str
        Source table path.
    source_sha256 : str
        Source table SHA-256.
    source_citation : str
        Source citation.
    price_sources : tuple of str
        Price sources used.
    cost_sources : tuple of str
        Cost sources used.
    assumptions : DiscountAssumptions
        Applied assumptions.
    revenue_per_ha : float or None
        Undiscounted revenue.
    cost_per_ha : float or None
        Undiscounted cost.
    discounted_revenue_per_ha : float or None
        Discounted revenue.
    discounted_cost_per_ha : float or None
        Discounted cost.
    npv_per_ha : float or None
        Net present value.
    site_value_per_ha : float or None
        Faustmann site value.
    benefit_cost_ratio : float or None
        Discounted benefit/cost ratio.
    revenue_lines : tuple of RevenueLine
        Priced product lines.
    cost_lines : tuple of CostLine
        Cost lines.
    cash_flows : tuple of CashFlow
        Escalated and discounted flows.
    gaps : tuple of EconomicGap
        Explicit gaps.
    evidence : str, optional
        Result label. Defaults to ``"reimplemented"``.
    validation : str, optional
        Validation status. Defaults to ``"unvalidated"``.
    """

    species_code: str
    age: float
    period: str
    source_model: str
    source_version: str
    source_relative_path: str
    source_sha256: str
    source_citation: str
    price_sources: tuple[str, ...]
    cost_sources: tuple[str, ...]
    assumptions: DiscountAssumptions
    revenue_per_ha: float | None
    cost_per_ha: float | None
    discounted_revenue_per_ha: float | None
    discounted_cost_per_ha: float | None
    npv_per_ha: float | None
    site_value_per_ha: float | None
    benefit_cost_ratio: float | None
    revenue_lines: tuple[RevenueLine, ...]
    cost_lines: tuple[CostLine, ...]
    cash_flows: tuple[CashFlow, ...]
    gaps: tuple[EconomicGap, ...]
    evidence: str = "reimplemented"
    validation: str = "unvalidated"

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-ready economic result.

        Returns
        -------
        dict of str to object
            Economic result fields.
        """
        return {
            "species_code": self.species_code,
            "age": self.age,
            "period": self.period,
            "provenance": {
                "source_model": self.source_model,
                "source_version": self.source_version,
                "relative_path": self.source_relative_path,
                "sha256": self.source_sha256,
                "citation": self.source_citation,
            },
            "price_sources": list(self.price_sources),
            "cost_sources": list(self.cost_sources),
            "assumptions": self.assumptions.as_dict(),
            "revenue_per_ha": self.revenue_per_ha,
            "cost_per_ha": self.cost_per_ha,
            "discounted_revenue_per_ha": self.discounted_revenue_per_ha,
            "discounted_cost_per_ha": self.discounted_cost_per_ha,
            "npv_per_ha": self.npv_per_ha,
            "site_value_per_ha": self.site_value_per_ha,
            "benefit_cost_ratio": self.benefit_cost_ratio,
            "revenue_lines": [line.as_dict() for line in self.revenue_lines],
            "cost_lines": [line.as_dict() for line in self.cost_lines],
            "cash_flows": [flow.as_dict() for flow in self.cash_flows],
            "gaps": [gap.as_dict() for gap in self.gaps],
            "evidence": self.evidence,
            "validation": self.validation,
        }


@dataclass(frozen=True)
class SensitivityCase:
    """One price, cost, or discount sensitivity case.

    Parameters
    ----------
    name : str
        Case name.
    price_multiplier : float, optional
        Multiplier on all product revenue. Defaults to 1.
    cost_multiplier : float, optional
        Multiplier on selected costs. Defaults to 1.
    discount_rate_delta : float, optional
        Additive change to the discount rate as a fraction. Defaults to 0.
    cost_categories : tuple of CostCategory, optional
        Categories affected by ``cost_multiplier``. Empty means all costs.
    """

    name: str
    price_multiplier: float = 1.0
    cost_multiplier: float = 1.0
    discount_rate_delta: float = 0.0
    cost_categories: tuple[CostCategory, ...] = ()

    def __post_init__(self) -> None:
        """Validate the sensitivity case.

        Raises
        ------
        InvalidEconomicsInputError
            When a value is malformed.
        """
        _text(self.name, "name")
        for name, value in (
            ("price_multiplier", self.price_multiplier),
            ("cost_multiplier", self.cost_multiplier),
            ("discount_rate_delta", self.discount_rate_delta),
        ):
            _finite(value, name)
        if self.price_multiplier < 0:
            message = "price_multiplier must be non-negative"
            raise InvalidEconomicsInputError(message)
        if self.cost_multiplier < 0:
            message = "cost_multiplier must be non-negative"
            raise InvalidEconomicsInputError(message)

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-ready sensitivity case.

        Returns
        -------
        dict of str to object
            Case fields.
        """
        return {
            "name": self.name,
            "price_multiplier": self.price_multiplier,
            "cost_multiplier": self.cost_multiplier,
            "discount_rate_delta": self.discount_rate_delta,
            "cost_categories": [category.value for category in self.cost_categories],
        }


@dataclass(frozen=True)
class SensitivityCaseResult:
    """One evaluated sensitivity case.

    Parameters
    ----------
    case : SensitivityCase
        Case definition.
    result : EconomicResult
        Evaluated result.
    npv_change_per_ha : float or None
        Change from the base NPV.
    direction : str
        ``"increase"``, ``"decrease"``, ``"unchanged"``, or ``"unavailable"``.
    """

    case: SensitivityCase
    result: EconomicResult
    npv_change_per_ha: float | None
    direction: str

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-ready case result.

        Returns
        -------
        dict of str to object
            Case result fields.
        """
        return {
            "case": self.case.as_dict(),
            "result": self.result.as_dict(),
            "npv_change_per_ha": self.npv_change_per_ha,
            "direction": self.direction,
        }


@dataclass(frozen=True)
class SensitivityResult:
    """A base result and its sensitivity cases.

    Parameters
    ----------
    base : EconomicResult
        Base result.
    cases : tuple of SensitivityCaseResult
        Evaluated cases.
    """

    base: EconomicResult
    cases: tuple[SensitivityCaseResult, ...]

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-ready sensitivity result.

        Returns
        -------
        dict of str to object
            Base and cases.
        """
        return {
            "base": self.base.as_dict(),
            "cases": [case.as_dict() for case in self.cases],
        }


def fansier_sensitivity_cases() -> tuple[SensitivityCase, ...]:
    """Return FAN$IER-style price, cost, and discount cases.

    Returns
    -------
    tuple of SensitivityCase
        Ten cases: +/-1% discount, +/-10% regeneration, post-regeneration,
        conversion, and revenue.
    """
    conversion = (
        CostCategory.HARVEST,
        CostCategory.COMMERCIAL_THIN,
        CostCategory.TRANSPORT,
        CostCategory.MILLING,
        CostCategory.ROADS,
        CostCategory.ANNUAL,
    )
    return (
        SensitivityCase("discount_plus_1", discount_rate_delta=0.01),
        SensitivityCase("discount_minus_1", discount_rate_delta=-0.01),
        SensitivityCase(
            "regen_plus_10",
            cost_multiplier=1.1,
            cost_categories=(CostCategory.REGENERATION,),
        ),
        SensitivityCase(
            "regen_minus_10",
            cost_multiplier=0.9,
            cost_categories=(CostCategory.REGENERATION,),
        ),
        SensitivityCase(
            "post_regen_plus_10",
            cost_multiplier=1.1,
            cost_categories=(CostCategory.POST_REGENERATION,),
        ),
        SensitivityCase(
            "post_regen_minus_10",
            cost_multiplier=0.9,
            cost_categories=(CostCategory.POST_REGENERATION,),
        ),
        SensitivityCase(
            "conversion_plus_10",
            cost_multiplier=1.1,
            cost_categories=conversion,
        ),
        SensitivityCase(
            "conversion_minus_10",
            cost_multiplier=0.9,
            cost_categories=conversion,
        ),
        SensitivityCase("revenue_plus_10", price_multiplier=1.1),
        SensitivityCase("revenue_minus_10", price_multiplier=0.9),
    )

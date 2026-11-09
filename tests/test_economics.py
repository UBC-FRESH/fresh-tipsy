"""Tests for explicit product prices, costs, NPV, and sensitivity."""

from __future__ import annotations

import pytest

from fresh_tipsy.curves import Provenance
from fresh_tipsy.economics import (
    AmbiguousPriceError,
    CostCategory,
    CostEntry,
    DiscountAssumptions,
    EconomicsRequest,
    InvalidEconomicsInputError,
    MissingPriceError,
    PriceBook,
    PriceEntry,
    PriceKey,
    SensitivityCase,
    UnitMismatchError,
    evaluate_economics,
    evaluate_sensitivity,
    fansier_sensitivity_cases,
)
from fresh_tipsy.products import (
    ProductGroup,
    ProductQuantity,
    ProductRecovery,
    ProductTotals,
    product_field,
)

_CITATION = "test citation"


def _provenance() -> Provenance:
    """Return a source provenance fixture."""
    return Provenance(
        asset_id="asset",
        pair_id="pair",
        format="taf",
        source_model="TIPSY",
        source_version="4.5",
        source_build="test",
        database_title="test",
        relative_path="Database/fdc1050N00.taf",
        sha256="abc123",
        evidence="model_output",
        citation="test source citation",
    )


def _recovery(
    *,
    field_name: str = "Lumber_2_or_Better_2x4",
    quantity: float = 1000.0,
    age: float = 10.0,
) -> ProductRecovery:
    """Build a one-product recovery fixture."""
    field = product_field(field_name)
    quantity_value = ProductQuantity(field, quantity)
    values: dict[ProductGroup, tuple[ProductQuantity, ...]] = dict.fromkeys(ProductGroup, ())
    values[field.group] = (quantity_value,)
    return ProductRecovery(
        age=age,
        scenario="untreated",
        species_code="FDC",
        provenance=_provenance(),
        lumber_2_or_better=values[ProductGroup.LUMBER_2_OR_BETTER],
        residues=values[ProductGroup.RESIDUE],
        log_grades=values[ProductGroup.LOG_GRADE],
        graded_lumber=values[ProductGroup.LUMBER_GRADED],
        degraded_lumber=values[ProductGroup.LUMBER_DEGRADED],
        industrial_logs=values[ProductGroup.INDUSTRIAL_LOG],
        totals=ProductTotals(
            lumber_2_or_better_bf_ha=None,
            graded_bf_ha=None,
            degraded_bf_ha=None,
            logs_m3_ha=None,
            residues_odt_ha=None,
            industrial_m3_ha=None,
        ),
        checks=(),
    )


def _entry(
    *,
    group: ProductGroup = ProductGroup.LUMBER_2_OR_BETTER,
    price: float = 1000.0,
    unit: str = "CAD/mbf",
    dimension: str | None = None,
    period: str = "default",
) -> PriceEntry:
    """Build a price entry fixture."""
    return PriceEntry(
        key=PriceKey(
            "FDC",
            group,
            period=period,
            dimension=dimension,
        ),
        price_per_unit=price,
        unit=unit,
        source="test price",
        citation=_CITATION,
    )


def _cost(
    *,
    amount: float = 50.0,
    age: float = 0.0,
    category: CostCategory = CostCategory.REGENERATION,
) -> CostEntry:
    """Build a cost entry fixture."""
    return CostEntry(
        category=category,
        age=age,
        amount_per_ha=amount,
        label="test cost",
        source="test cost",
        citation=_CITATION,
    )


def _request(
    *,
    recovery: ProductRecovery | None = None,
    book: PriceBook | None = None,
    costs: tuple[CostEntry, ...] = (),
    assumptions: DiscountAssumptions | None = None,
    period: str = "default",
    revenue_groups: tuple[ProductGroup, ...] = (ProductGroup.LUMBER_2_OR_BETTER,),
) -> EconomicsRequest:
    """Build an economics request fixture."""
    return EconomicsRequest(
        recovery=recovery or _recovery(),
        price_book=book or PriceBook((_entry(),)),
        assumptions=assumptions or DiscountAssumptions(0.10),
        revenue_groups=revenue_groups,
        costs=costs,
        period=period,
    )


def test_hand_checked_npv_and_site_value() -> None:
    """NPV and site value match a hand-checked discounted cash flow."""
    result = evaluate_economics(_request(costs=(_cost(amount=50.0, age=0.0),)))
    assert result.revenue_per_ha == 1000.0
    assert result.cost_per_ha == 50.0
    assert result.discounted_revenue_per_ha == pytest.approx(385.543289, abs=1e-6)
    assert result.discounted_cost_per_ha == 50.0
    assert result.npv_per_ha == pytest.approx(335.543289, abs=1e-6)
    assert result.site_value_per_ha == pytest.approx(546.081251, abs=1e-6)
    assert result.benefit_cost_ratio == pytest.approx(7.710866, abs=1e-6)
    assert result.evidence == "reimplemented"
    assert result.validation == "unvalidated"
    assert result.price_sources == ("test price",)
    assert result.cost_sources == ("test cost",)
    assert len(result.revenue_lines) == 1
    assert len(result.cash_flows) == 2
    assert result.as_dict()["npv_per_ha"] == pytest.approx(335.543289, abs=1e-6)


def test_real_price_and_cost_escalation() -> None:
    """Real escalation compounds for the stated duration."""
    assumptions = DiscountAssumptions(
        0.10,
        real_price_increase=0.10,
        real_cost_increase=0.10,
        real_increase_duration=2.0,
    )
    result = evaluate_economics(
        _request(
            costs=(_cost(amount=50.0, age=10.0),),
            assumptions=assumptions,
        )
    )
    assert result.revenue_lines[0].revenue_per_ha == 1000.0
    flows = {flow.kind: flow for flow in result.cash_flows}
    assert flows["revenue"].escalated_per_ha == pytest.approx(1210.0)
    assert flows["cost"].escalated_per_ha == pytest.approx(60.5)
    assert result.npv_per_ha == pytest.approx(443.182011, abs=1e-6)


def test_zero_duration_has_no_escalation() -> None:
    """A zero real-increase duration leaves cash flows unchanged."""
    assumptions = DiscountAssumptions(0.10, real_price_increase=0.10, real_increase_duration=0.0)
    result = evaluate_economics(_request(assumptions=assumptions))
    assert result.npv_per_ha == pytest.approx(385.543289, abs=1e-6)


def test_price_lookup_prefers_specific_entry() -> None:
    """A dimension-specific price beats a wildcard price."""
    book = PriceBook(
        (
            _entry(price=1000.0),
            _entry(price=500.0, dimension="2x4"),
        )
    )
    assert (
        book.lookup(
            PriceKey("FDC", ProductGroup.LUMBER_2_OR_BETTER, dimension="2x4")
        ).price_per_unit
        == 500.0
    )
    assert (
        book.lookup(
            PriceKey("FDC", ProductGroup.LUMBER_2_OR_BETTER, dimension="2x6")
        ).price_per_unit
        == 1000.0
    )
    assert book.as_dict()["entries"]


def test_price_lookup_missing_and_ambiguous() -> None:
    """Missing and ambiguous prices fail explicitly."""
    book = PriceBook((_entry(period="old"),))
    with pytest.raises(MissingPriceError, match="no price"):
        book.lookup(PriceKey("FDC", ProductGroup.LUMBER_2_OR_BETTER, period="new"))
    ambiguous = PriceBook((_entry(), _entry(price=900.0)))
    with pytest.raises(AmbiguousPriceError, match="ambiguous"):
        ambiguous.lookup(PriceKey("FDC", ProductGroup.LUMBER_2_OR_BETTER))


def test_missing_price_is_an_explicit_gap() -> None:
    """A missing price makes revenue unavailable, not zero."""
    result = evaluate_economics(_request(book=PriceBook()))
    assert result.revenue_per_ha is None
    assert result.npv_per_ha is None
    assert result.revenue_lines == ()
    assert result.gaps[0].code == "missing_price"
    assert result.gaps[0].product == "Lumber_2_or_Better_2x4"


def test_unit_mismatch_is_an_explicit_gap() -> None:
    """An incompatible price unit is a gap, not zero revenue."""
    result = evaluate_economics(
        _request(
            recovery=_recovery(field_name="Residual_Chips", quantity=10.0),
            revenue_groups=(ProductGroup.RESIDUE,),
            book=PriceBook(
                (
                    _entry(
                        group=ProductGroup.RESIDUE,
                        price=50.0,
                        unit="CAD/BDU",
                    ),
                )
            ),
        )
    )
    assert result.revenue_per_ha is None
    assert result.gaps[0].code == "unit_mismatch"


def test_ambiguous_price_is_an_explicit_gap() -> None:
    """An ambiguous price is reported instead of guessed."""
    result = evaluate_economics(_request(book=PriceBook((_entry(), _entry(price=900.0)))))
    assert result.revenue_per_ha is None
    assert result.gaps[0].code == "ambiguous_price"


def test_zero_product_quantity_does_not_require_a_price() -> None:
    """Zero product quantities are skipped without a missing-price gap."""
    result = evaluate_economics(_request(recovery=_recovery(quantity=0.0), book=PriceBook()))
    assert result.revenue_per_ha == 0.0
    assert result.npv_per_ha == 0.0
    assert result.gaps == ()


def test_unit_factor_errors() -> None:
    """Malformed and incompatible unit strings raise explicit errors."""
    from fresh_tipsy.economics.engine import _unit_factor

    with pytest.raises(UnitMismatchError, match="CAD"):
        _unit_factor("USD/mbf", "bf/ha")
    with pytest.raises(UnitMismatchError, match="/ha"):
        _unit_factor("CAD/mbf", "bf")
    with pytest.raises(UnitMismatchError, match="unsupported"):
        _unit_factor("CAD/BDU", "ODT/ha")
    with pytest.raises(UnitMismatchError, match="cannot price"):
        _unit_factor("CAD/m3", "bf/ha")


def test_unselected_groups_are_not_priced() -> None:
    """Only explicitly selected product groups contribute revenue."""
    result = evaluate_economics(
        _request(
            recovery=_recovery(field_name="Residual_Chips", quantity=10.0),
            book=PriceBook(),
            revenue_groups=(ProductGroup.LUMBER_2_OR_BETTER,),
        )
    )
    assert result.revenue_per_ha == 0.0
    assert result.gaps == ()


@pytest.mark.parametrize(
    ("field_name", "quantity", "price", "unit", "expected"),
    [
        ("Lumber_2_or_Better_2x4", 1000.0, 1000.0, "CAD/mbf", 1000.0),
        ("Logs_Grade_D", 3.0, 100.0, "CAD/m³", 300.0),
        ("Residual_Chips", 2.0, 100.0, "CAD/ODT", 200.0),
    ],
)
def test_compatible_units(
    field_name: str,
    quantity: float,
    price: float,
    unit: str,
    expected: float,
) -> None:
    """Compatible price units produce revenue."""
    field = product_field(field_name)
    result = evaluate_economics(
        _request(
            recovery=_recovery(field_name=field_name, quantity=quantity),
            revenue_groups=(field.group,),
            book=PriceBook(
                (
                    _entry(
                        group=field.group,
                        price=price,
                        unit=unit,
                    ),
                )
            ),
        )
    )
    assert result.revenue_per_ha == expected


def test_sensitivity_directions() -> None:
    """Revenue, cost, and discount sensitivity move in expected directions."""
    result = evaluate_sensitivity(_request(costs=(_cost(),)), fansier_sensitivity_cases())
    assert len(result.cases) == 10
    directions = {case.case.name: case.direction for case in result.cases}
    assert directions["revenue_plus_10"] == "increase"
    assert directions["revenue_minus_10"] == "decrease"
    assert directions["regen_plus_10"] == "decrease"
    assert directions["regen_minus_10"] == "increase"
    assert directions["discount_plus_1"] == "decrease"
    assert directions["discount_minus_1"] == "increase"
    assert directions["post_regen_plus_10"] == "unchanged"
    data = result.as_dict()
    base = data["base"]
    assert isinstance(base, dict)
    assert base["npv_per_ha"] == pytest.approx(335.543289, abs=1e-6)


def test_sensitivity_unavailable_and_negative_rate() -> None:
    """Missing prices make cases unavailable; negative rates are rejected."""
    result = evaluate_sensitivity(
        _request(book=PriceBook()),
        (SensitivityCase("revenue_plus_10", price_multiplier=1.1),),
    )
    assert result.cases[0].direction == "unavailable"
    assert result.cases[0].npv_change_per_ha is None
    with pytest.raises(InvalidEconomicsInputError, match="negative discount"):
        evaluate_sensitivity(
            _request(),
            (SensitivityCase("bad_discount", discount_rate_delta=-0.2),),
        )


def test_sensitivity_price_delta_matches_discounted_revenue() -> None:
    """A 10% price change equals 10% of discounted revenue."""
    result = evaluate_sensitivity(
        _request(costs=(_cost(),)),
        (SensitivityCase("revenue_plus_10", price_multiplier=1.1),),
    )
    assert result.cases[0].npv_change_per_ha == pytest.approx(38.554329, abs=1e-6)


def test_cost_only_npv_boundary() -> None:
    """No product revenue produces a negative cost-only NPV."""
    result = evaluate_economics(
        _request(
            recovery=_recovery(quantity=0.0),
            book=PriceBook(),
            costs=(_cost(amount=25.0),),
        )
    )
    assert result.revenue_per_ha == 0.0
    assert result.npv_per_ha == -25.0
    assert result.gaps == ()


def test_base_age_and_sunk_costs() -> None:
    """Costs before the base age are ignored unless explicitly included."""
    assumptions = DiscountAssumptions(0.10, base_age=5.0)
    result = evaluate_economics(
        _request(costs=(_cost(amount=50.0, age=0.0),), assumptions=assumptions)
    )
    assert result.npv_per_ha == pytest.approx(620.921323, abs=1e-6)
    included = evaluate_economics(
        _request(
            costs=(_cost(amount=50.0, age=0.0),),
            assumptions=DiscountAssumptions(0.10, base_age=5.0, include_sunk_costs=True),
        )
    )
    assert included.npv_per_ha == pytest.approx(540.395823, abs=1e-6)


def test_site_value_unavailable_at_zero_discount() -> None:
    """Site value is unavailable without a positive discount rate."""
    result = evaluate_economics(_request(assumptions=DiscountAssumptions(0.0)))
    assert result.npv_per_ha == 1000.0
    assert result.site_value_per_ha is None
    assert result.gaps[-1].code == "site_value_unavailable"
    assert result.gaps[-1].as_dict()["code"] == "site_value_unavailable"


def test_revenue_before_base_age_is_ignored() -> None:
    """A harvest before the base age contributes no discounted revenue."""
    result = evaluate_economics(_request(assumptions=DiscountAssumptions(0.10, base_age=20.0)))
    assert result.revenue_per_ha == 1000.0
    assert result.discounted_revenue_per_ha == 0.0
    assert result.npv_per_ha == 0.0


def test_no_costs_has_no_benefit_cost_ratio() -> None:
    """A zero discounted cost has no benefit/cost ratio."""
    result = evaluate_economics(_request())
    assert result.discounted_cost_per_ha == 0.0
    assert result.benefit_cost_ratio is None


def test_cost_entry_as_dict() -> None:
    """Cost entries serialize their category and evidence."""
    data = _cost(category=CostCategory.HARVEST).as_dict()
    assert data["category"] == "harvest"
    assert data["evidence"] == "assumption"


def test_fansier_defaults_are_cited() -> None:
    """The FAN$IER default discount rate is cited, not hidden."""
    assumptions = DiscountAssumptions.fansier_defaults()
    assert assumptions.discount_rate == 0.04
    assert "4% default discount rate" in assumptions.citation
    assert assumptions.as_dict()["discount_rate"] == 0.04


def test_input_validation() -> None:
    """Malformed economic inputs fail explicitly."""
    with pytest.raises(InvalidEconomicsInputError, match="species_code"):
        PriceKey("", ProductGroup.LUMBER_2_OR_BETTER)
    with pytest.raises(InvalidEconomicsInputError, match="price_per_unit"):
        _entry(price=-1.0)
    with pytest.raises(InvalidEconomicsInputError, match="age"):
        _cost(age=-1.0)
    with pytest.raises(InvalidEconomicsInputError, match="amount_per_ha"):
        _cost(amount=-1.0)
    with pytest.raises(InvalidEconomicsInputError, match="finite"):
        CostEntry(
            category=CostCategory.REGENERATION,
            age=float("nan"),
            amount_per_ha=1.0,
            label="bad",
            source="test",
            citation=_CITATION,
        )
    with pytest.raises(InvalidEconomicsInputError, match="discount_rate"):
        DiscountAssumptions(-0.1)
    with pytest.raises(InvalidEconomicsInputError, match="real_price_increase"):
        DiscountAssumptions(0.04, real_price_increase=-1.0)
    with pytest.raises(InvalidEconomicsInputError, match="real_increase_duration"):
        DiscountAssumptions(0.04, real_increase_duration=-1.0)
    with pytest.raises(InvalidEconomicsInputError, match="base_age"):
        DiscountAssumptions(0.04, base_age=-1.0)
    with pytest.raises(InvalidEconomicsInputError, match="price_multiplier"):
        SensitivityCase("bad", price_multiplier=-1.0)
    with pytest.raises(InvalidEconomicsInputError, match="cost_multiplier"):
        SensitivityCase("bad", cost_multiplier=-1.0)
    with pytest.raises(InvalidEconomicsInputError, match="period"):
        _request(period=" ")
    with pytest.raises(InvalidEconomicsInputError, match="lumber basis"):
        _request(
            revenue_groups=(
                ProductGroup.LUMBER_2_OR_BETTER,
                ProductGroup.LUMBER_GRADED,
            )
        )
    with pytest.raises(InvalidEconomicsInputError, match="duplicates"):
        _request(
            revenue_groups=(
                ProductGroup.LUMBER_2_OR_BETTER,
                ProductGroup.LUMBER_2_OR_BETTER,
            )
        )

# Economics (P4.4)

Date: 2026-11-09
Status: complete, reimplemented and unvalidated against FAN$IER
Scope: explicit prices and costs, product revenue, NPV, site value, and sensitivity
Related: [`product-recovery.md`](product-recovery.md), [`fansier-scope.md`](fansier-scope.md), [`../../src/fresh_tipsy/economics/`](../../src/fresh_tipsy/economics/)

## Boundary

This is a documented FAN$IER-style calculation, not a FAN$IER reproduction.
Every result is labelled `reimplemented` and `unvalidated`. No FAN$IER golden
output exists, its price and cost tables have not been parsed, and no parity is
claimed.

The growth-side product quantities are still TASS/SYLVER `model_output`. The
economics layer adds only explicit user inputs and reimplemented formulas.

## Explicit inputs

```python
from fresh_tipsy.economics import (
    CostCategory,
    CostEntry,
    DiscountAssumptions,
    EconomicsRequest,
    PriceBook,
    PriceEntry,
    PriceKey,
    evaluate_economics,
)
from fresh_tipsy.products import ProductGroup

price = PriceEntry(
    key=PriceKey("FDC", ProductGroup.LUMBER_2_OR_BETTER, dimension="2x4"),
    price_per_unit=1000.0,
    unit="CAD/mbf",
    source="user price",
    citation="User-supplied 2026 assumption; replace with a sourced price.",
)
cost = CostEntry(
    category=CostCategory.REGENERATION,
    age=0.0,
    amount_per_ha=50.0,
    label="site preparation",
    source="user cost",
    citation="User-supplied assumption.",
)
request = EconomicsRequest(
    recovery=recovery,
    price_book=PriceBook((price,)),
    revenue_groups=(ProductGroup.LUMBER_2_OR_BETTER, ProductGroup.RESIDUE),
    costs=(cost,),
    assumptions=DiscountAssumptions(discount_rate=0.10),
)
result = evaluate_economics(request)
```

A price key matches species, group, period, and optional grade, dimension, or
detail. Omitted grade/dimension/detail values are wildcards; the most specific
match wins. An ambiguous match or a missing price is an explicit gap.

`revenue_groups` is required. Select one lumber basis—`LUMBER_2_OR_BETTER`,
`LUMBER_GRADED`, or `LUMBER_DEGRADED`—and add residues if they are part of the
chosen product suite. The three lumber views describe overlapping volumes, so
selecting more than one raises an error instead of double counting. Coast log
or industrial-log analyses select their own groups.

Supported price units are `CAD/bf`, `CAD/mbf`, `CAD/m3` (`CAD/m³`), and
`CAD/ODT`. Board-foot and thousand-board-foot units convert with the standard
1000 factor. ODT-to-BDU or other physical conversions are not applied without
an explicit source factor, so those prices produce a `unit_mismatch` gap.

Cost categories align with the FAN$IER sections: regeneration,
post-regeneration, harvest, commercial thin, transport, milling, roads, annual,
and other. Costs are explicit CAD/ha amounts at explicit ages. No default cost
table is embedded.

## Discount assumptions

`DiscountAssumptions` requires an explicit discount rate. The cited FAN$IER
default is available through `DiscountAssumptions.fansier_defaults()`:

- 4% real discount rate;
- 0% real price increase;
- 0% real cost increase;
- 25-year real-increase duration;
- base age zero.

Source: FAN$IER Help, *Discount Assumptions* (2016). The default is a cited
public default, not an invented coefficient.

## Formulas

For flow at age `t`, base age `b`, real increase `i` with duration `d`, and
discount rate `r`:

```text
escalated(t) = amount(t) * (1 + i) ** min(t, d)
present(t)   = escalated(t) * (1 + r) ** (b - t)
```

Flows before `b` are ignored unless `include_sunk_costs` is true. When included,
they are compounded forward to the base age.

```text
NPV = sum(present revenue) - sum(present cost)
SV  = NPV * (1 + r) ** A / ((1 + r) ** A - 1)
```

`A` is the harvest age. Site value is `unavailable` when `r <= 0` or
`A <= 0`. `B/C` is discounted revenue divided by discounted cost, or
unavailable when discounted cost is zero.

## Hand-checked case

Inputs:

- revenue: 1000 CAD/ha at age 10;
- cost: 50 CAD/ha at age 0;
- discount rate: 10%;
- no real escalation;
- base age: 0.

Results:

```text
discounted revenue = 1000 / 1.1**10 = 385.543289
discounted cost    = 50               = 50.000000
NPV                = 385.543289 - 50  = 335.543289
SV                 = 335.543289 * 1.1**10 / (1.1**10 - 1) = 546.081251
B/C                = 385.543289 / 50  = 7.710866
```

The case is asserted in `tests/test_economics.py`.

## Sensitivity

`fansier_sensitivity_cases()` returns ten cases:

- discount rate plus and minus 1 percentage point;
- regeneration cost plus and minus 10%;
- post-regeneration cost plus and minus 10%;
- conversion cost plus and minus 10% (harvest, commercial thin, transport,
  milling, roads, annual);
- revenue plus and minus 10%.

`evaluate_sensitivity` reports the case NPV, its change from the base, and a
direction: `increase`, `decrease`, `unchanged`, or `unavailable`.

## Gaps

- No parsed FAN$IER price or cost table and no validated FAN$IER golden output.
- No default product price or cost values are embedded.
- No ODT/BDU or other physical conversion factor is invented.
- No IRR, tax treatment, or mill-specific economics is implemented.
- No FAN$IER parity claim is made.

## Attribution

The FAN$IER concepts, discount defaults, product groups, and sensitivity
structure are attributed to the Province of British Columbia. `fresh-tipsy`
implements only the documented formulas and explicit inputs described here.

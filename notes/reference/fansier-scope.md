# FAN$IER scope and inventory

Date: 2026-11-09
Status: partial, public documentation and local TIPSY observations

## What FAN$IER is for

FAN$IER is the BC forest-economics layer. It consumes product yields and applies
product suites, prices, costs, discounting, and sensitivity analysis.

The target `fresh-tipsy` surface is:

```text
product prices
cost assumptions
product value
NPV / site value
sensitivity cases
```

## What is not yet parsed

The local TIPSY 4.5 install and a separate FAN$IER executable are present in
the recorded source tree. FAN$IER's internal data tables have not been parsed.
Phase 1 must inventory:

- the FAN$IER install root;
- product-suite definitions;
- default price tables;
- cost tables;
- report templates;
- sample `.fns`, `.rgm`, or equivalent project files;
- any exported report formats.

If FAN$IER is not available locally, the economics layer starts from public
FAN$IER documentation and is labelled `reimplemented`.

## Public product facts already identified

From the public FAN$IER help:

- TIPSY lumber grades: `SS`, `#1`, `#2`, `#3`, `#4`;
- structural dimensions: `2x4`, `2x6`, `2x8`, `2x10`;
- TIPSY residues: chips, sawdust, shavings, trims, bark;
- TASS III lumber is ungraded by dimension;
- juvenile-wood degrade table is published but labelled tentative/educational;
- default price proxies are historical, not current market prices.

## Economics scope for the first release

Implement only documented, testable pieces:

1. Price lookup by species/group/product/period.
2. Simple product revenue from product quantities.
3. Transport, harvest, milling, and regeneration cost fields where public.
4. NPV with an explicit discount rate and time series.
5. Sensitivity runs for price, cost, and discount changes.

Do not claim:

- mill-specific economics;
- grade-specific prices without grade data;
- a full FAN$IER reproduction until golden outputs are available.

## Evidence labels

```text
source_table      price/cost table read directly
reimplemented     formula implemented from public documentation
validated_against matches a named FAN$IER output within tolerance
experimental      documented but not fully validated
unavailable       no source or runtime available
```

## Integration note

FAN$IER economics should remain optional. A growth-only or product-only user
must not be forced to install or run FAN$IER.

## P4.4 implementation status

The economic formulas and explicit-input layer are implemented in
[`economics.md`](economics.md). It provides price lookup, revenue, NPV, site
value, and sensitivity, but embeds no default price or cost table and claims no
FAN$IER parity. The unparsed FAN$IER tables and missing golden outputs remain
recording gaps.

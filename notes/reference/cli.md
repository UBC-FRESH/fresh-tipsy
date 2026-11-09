# Command-line interface (P5.1)

Date: 2026-11-09
Status: P5.1 complete
Scope: Typer command contracts for growth, product, and economics queries
Related: [`../../src/fresh_tipsy/cli.py`](../../src/fresh_tipsy/cli.py), [`testing.md`](testing.md), [`economics.md`](economics.md)

## Commands

All new commands support `--json`. JSON responses contain `status`, `query`,
`result`, `evidence`, and `warnings` where applicable. Human output is a short
summary, not a substitute for machine provenance.

```bash
fresh-tipsy db extract --source "$TIPSY_INSTALL" --out "$FRESH_TIPSY_CACHE"
fresh-tipsy db validate --catalog "$FRESH_TIPSY_CACHE/manifest.json"
fresh-tipsy db catalog --catalog "$FRESH_TIPSY_CACHE/manifest.json" --species PLI

fresh-tipsy curve query \
  --catalog "$FRESH_TIPSY_CACHE/manifest.json" \
  --source "$TIPSY_INSTALL" \
  --species PLI --site-index 20 --age 80 --pnc N --json

fresh-tipsy product recover \
  --catalog "$FRESH_TIPSY_CACHE/manifest.json" \
  --source "$TIPSY_INSTALL" \
  --species PLI --site-index 20 --age 80 --pnc N --json

fresh-tipsy econ run \
  --catalog "$FRESH_TIPSY_CACHE/manifest.json" \
  --source "$TIPSY_INSTALL" \
  --scenario scenario.json --json
```

`--source` is the install root used to resolve manifest-relative table paths.
If it is omitted, the CLI uses `TIPSY_INSTALL`; if neither is available the
command fails explicitly.

Exit codes:

- `0`: success.
- `1`: invalid input, unsupported query, missing manifest, mass-balance
  failure, or another user-facing error.
- `2`: Typer argument or option error.

## Economics scenario JSON

```json
{
  "query": {
    "species_code": "FDC",
    "site_index": 30,
    "age": 60,
    "pnc": "N",
    "format": "taf"
  },
  "period": "user-2026",
  "revenue_groups": ["lumber_2_or_better", "residue"],
  "prices": [
    {
      "species_code": "FDC",
      "group": "lumber_2_or_better",
      "period": "user-2026",
      "dimension": "2x4",
      "price_per_unit": 1000.0,
      "unit": "CAD/mbf",
      "source": "user price",
      "citation": "User-supplied assumption."
    }
  ],
  "costs": [
    {
      "category": "regeneration",
      "age": 0,
      "amount_per_ha": 1200.0,
      "label": "site preparation and planting",
      "source": "user cost",
      "citation": "User-supplied assumption."
    }
  ],
  "assumptions": {
    "discount_rate": 0.04,
    "real_price_increase": 0.0,
    "real_cost_increase": 0.0,
    "real_increase_duration": 25,
    "base_age": 0,
    "include_sunk_costs": false
  }
}
```

The scenario requires `query`, `revenue_groups`, and `assumptions.discount_rate`.
Prices and costs are explicit; no default price or cost table is embedded.
Missing prices, ambiguous matches, and incompatible units are returned as
warnings/gaps, and revenue/NPV can be `null`.

Only one lumber basis may appear in `revenue_groups`: `lumber_2_or_better`,
`lumber_graded`, or `lumber_degraded`. Add `residue` when it belongs to the
chosen product suite. Coast log or industrial-log scenarios select their own
groups.

## Boundaries

- Product values are TASS/SYLVER `model_output`, not measured field grades.
- Economics results are `reimplemented` and `unvalidated` against FAN$IER.
- The CLI does not expose a separate calculation path; it calls the typed
  curve, product, and economics functions.
- No raw table or normalized asset is written by these commands.

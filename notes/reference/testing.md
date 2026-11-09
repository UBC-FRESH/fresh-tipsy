# Testing fresh-tipsy

Date: 2026-11-09
Status: current test policy for P2 and later phases

## Run everything

```bash
python scripts/dashboard.py
```

The dashboard runs lint, format, strict types, tests with the coverage gate, the workflow validator, and the docs build.

## Test layers

| Layer | Location | What it checks |
| --- | --- | --- |
| Unit | `tests/test_*` | Parser, metadata, manifest, normalization, and catalog behavior |
| Contract | `tests/test_catalog.py`, `tests/test_manifest_io.py` | Public interfaces and the manifest schema |
| Integration | `tests/test_cli_db.py` | `db extract`, `db validate`, and `db catalog` |
| Property | `tests/test_properties_tables.py`, `tests/test_curve_properties.py` | Row counts, age ranges, slug stability, interpolation bounds, exact-age identity, and monotonicity |
| Product | `tests/test_product_schema.py`, `tests/test_product_recovery.py`, `tests/test_product_regression.py` | 77-field contract, aggregation, mass balance, missing dimensions, and real-source PLI checks |
| Economics | `tests/test_economics.py` | Explicit prices/costs, unit gaps, hand-checked NPV, site value, and sensitivity direction |
| Interface | `tests/test_cli_interfaces.py`, `tests/test_cli*.py`, `tests/test_api.py`, `tests/test_web.py` | CLI command contracts, JSON envelopes, exit codes, scenario validation, service functions, HTTP endpoints, and server-rendered views |
| Self-check | `tests/test_workflow.py` | The planning surfaces pass `scripts/check_workflow.py` |

## Synthetic fixtures

Committed parser fixtures live in [`../../tests/data/fixtures/synthetic/`](../../tests/data/fixtures/synthetic/). They are synthetic, not BC data, and must not be used for golden validation. They exercise the 22/151 field counts, two run blocks, and a PCT boundary.

## Real-source tests

Real-source tests skip when `TIPSY_DATABASE` is unset. To run them:

```bash
TIPSY_DATABASE="$TIPSY_INSTALL/Database" python -m pytest \
  tests/test_tab_parser.py tests/test_taf_parser.py \
  tests/test_catalog.py tests/test_normalized.py tests/test_cli_db.py \
  tests/test_product_regression.py tests/test_product_goldens.py -q
```

The tests read the installed tables, verify checksums and pair structure, and never copy raw tables into the repository. A missing install is a skip, not a pass of the real-data path.

The PLI product regression test checks ages 36, 55, and 91 for passing mass balances and provenance. Real-source product checks are skipped when `TIPSY_DATABASE` is unset.

FAN$IER golden tests are not present. The economics tests use explicit synthetic inputs and do not claim FAN$IER parity.

## Coverage gate

The gate covers both the workflow scripts and the package:

```text
scripts/check_workflow.py
scripts/dashboard.py
src/fresh_tipsy/
```

`--cov-fail-under=95` applies to the combined branch coverage. As of P5.3 the combined result is about 95.9 percent; `products/` and `economics/` are at 100 percent branch coverage. P2.6 extended the gate from `scripts/` to `src/fresh_tipsy/`; P3.5 added curve property and regression tests; P4.5 added product and economics regression, boundary, and missing-data tests; P5.1 added CLI contract tests; P5.2 added service and API tests; P5.3 added web route tests.

## No raw data in tests

- Tests use synthetic fixtures or a local install reached through `TIPSY_DATABASE`.
- A test must not commit a raw `.tab`, `.taf`, `.fns`, or `.brs` file.
- A test must not commit a normalized Parquet/CSV asset. Use `tmp_path` for those.
- A fixture must carry its source metadata and a clear synthetic-or-unavailable label.

## Attribution

Real-source runs read BC government data. The test output may cite a table path; it does not relicense the source. Cite TIPSY/FAN$IER and the source table in any published result.

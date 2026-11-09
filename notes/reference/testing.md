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
| Property | `tests/test_properties_tables.py` | Row counts, age ranges, slug stability, and normalization invariants |
| Self-check | `tests/test_workflow.py` | The planning surfaces pass `scripts/check_workflow.py` |

## Synthetic fixtures

Committed parser fixtures live in [`../../tests/data/fixtures/synthetic/`](../../tests/data/fixtures/synthetic/). They are synthetic, not BC data, and must not be used for golden validation. They exercise the 22/151 field counts, two run blocks, and a PCT boundary.

## Real-source tests

Real-source tests skip when `TIPSY_DATABASE` is unset. To run them:

```bash
TIPSY_DATABASE="$TIPSY_INSTALL/Database" python -m pytest \
  tests/test_tab_parser.py tests/test_taf_parser.py \
  tests/test_catalog.py tests/test_normalized.py tests/test_cli_db.py -q
```

The tests read the installed tables, verify checksums and pair structure, and never copy raw tables into the repository. A missing install is a skip, not a pass of the real-data path.

FAN$IER tests are not present yet. When they land, use `FANSIER_INSTALL` and the same skip-when-unset pattern.

## Coverage gate

The gate covers both the workflow scripts and the package:

```text
scripts/check_workflow.py
scripts/dashboard.py
src/fresh_tipsy/
```

`--cov-fail-under=95` applies to the combined branch coverage. As of P2.6 the combined result is about 97.6 percent. The old gate covered `scripts/` only; P2.6 extended it to `src/fresh_tipsy/` and recorded the change in `CHANGE_LOG.md`.

## No raw data in tests

- Tests use synthetic fixtures or a local install reached through `TIPSY_DATABASE`.
- A test must not commit a raw `.tab`, `.taf`, `.fns`, or `.brs` file.
- A test must not commit a normalized Parquet/CSV asset. Use `tmp_path` for those.
- A fixture must carry its source metadata and a clear synthetic-or-unavailable label.

## Attribution

Real-source runs read BC government data. The test output may cite a table path; it does not relicense the source. Cite TIPSY/FAN$IER and the source table in any published result.

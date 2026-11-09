# Validation, release, and FEMIC integration plan

Date: 2026-11-09
Status: draft

## Validation ladder

### Table extraction

- Raw file SHA256 matches the manifest.
- Field count matches the declared grammar.
- Header metadata matches inferred filename metadata.
- Age column is strictly increasing.
- Site-index range and PNC/stock-height variants are explicit.
- No duplicate table IDs.
- Normalized row count matches the raw data block.

### Growth queries

- Query a table at a raw age returns the raw value exactly.
- Interpolation between ages is monotonic and bounded.
- A query outside the table's site range fails explicitly.
- A query against a known species/site/age matches a golden TIPSY or FEMIC
  output within a stated tolerance.
- The same query through Python, CLI, API, and web returns the same value.

### Product recovery

- Lumber grade × dimension sums to the reported lumber total.
- Residue categories reconcile with the source total where available.
- Product volume plus loss reconciles with the input volume.
- No product output appears without a source and evidence label.
- Grade output is labelled `model_output`, not `field_grade`.

### Economics

- Prices are traceable to a source profile and period.
- NPV equals the documented discounted cash-flow formula on a hand-checked case.
- Sensitivity changes move in the expected direction.
- Missing price data produces an explicit gap, not zero.

### Interfaces

- CLI snapshots for help, success, and error paths.
- API contract tests for status codes and schema.
- Web smoke tests for catalog, curve, product, economics, and provenance views.
- Assistant tools tested with a fake provider; no network required.
- Every assistant response test asserts that provenance is present.

## Golden evidence

Store golden fixtures for:

- one `.tab` table;
- one `.taf` table;
- one full TIPSY output with lumber, residues, log grades, and LRF columns;
- one FAN$IER price/cost/NPV scenario;
- one FEMIC TSR output used for growth comparison.

Golden files are small, licensed for redistribution, and carry source metadata.
If a golden output cannot be redistributed, store only a checksum and a
reproduction command.

## Package release

Artifacts:

```text
fresh-tipsy wheel + sdist
fresh-tipsy-data manifest
normalized Parquet/CSV assets
checksums
citation file
known-gaps list
```

Release checks:

```text
python -m build
pip install dist/*.whl in a clean environment
fresh-tipsy --help
fresh-tipsy db validate
pytest
sphinx-build -b html docs _build/html -W
python scripts/check_workflow.py
```

## Data asset release

- Raw source files are not redistributed.
- Normalized assets are released with a manifest and citation.
- Each asset records the source version and extraction command.
- A user can rebuild the assets from a local TIPSY/FAN$IER install.
- If redistribution terms differ for a table, publish the manifest and rebuild
  instructions instead of the table.

## FEMIC integration

1. Publish `fresh-tipsy` as a package.
2. Add an optional dependency in FEMIC.
3. Add a thin adapter in FEMIC that calls `query_curve`, `recover_products`, or
   `run_economics`.
4. Pass `fresh-tipsy` provenance through FEMIC outputs.
5. Add a FEMIC integration test that works with a tiny fixture and skips when the
   optional package is absent.
6. Back-link the dependency in FEMIC docs and changelog.

## Release gates

- All parser and catalog tests pass.
- Golden growth, product, and economics checks pass.
- CLI/API/web/assistant tests pass.
- No raw data or personal paths in tracked files.
- Attribution appears in README, docs, API responses, and CLI `--json`.
- The package installs in a clean environment.
- The data manifest is stable and checksummed.

## Known gaps to record at release

- Which TIPSY/FAN$IER versions and tables are covered.
- Which product outputs are extracted versus reimplemented.
- Which economics assumptions are reimplemented and which are absent.
- Which species/site ranges are unsupported.
- Any runtime limitations on the host.

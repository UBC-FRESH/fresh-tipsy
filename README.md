# fresh-tipsy

A public, tested Python package for reading TIPSY and FAN$IER data tables,
exposing growth, product-recovery, and economics workflows, and preserving the
provenance of every value.

`fresh-tipsy` is a reimplementation and interoperability layer. It does not
claim authorship of TIPSY, FAN$IER, TASS, FEMIC, or BC government data. It exists
so those models and tables can be queried from Python, tested in the open, and
used by tools such as FEMIC without a GUI boundary.

Repository: <https://github.com/UBC-FRESH/fresh-tipsy>

## Status

Version 0.1.0 was released on 2026-11-09.
`ROADMAP.md` and GitHub issues carry the live status. The package is an
interoperability layer over precomputed TASS/TIPSY tables, not a TASS rewrite.

## Features

- `.tab`/`.taf` parsers, provenance manifests, catalog, and normalization.
- Typed growth queries over precomputed TASS/TIPSY tables, with interpolation,
  metrics, source SHA-256, and explicit unavailable metrics.
- Product recovery for lumber, residues, log grades, graded/degraded lumber, and
  industrial logs, with strict mass-balance checks.
- Explicit-input product economics: prices, costs, NPV, Faustmann site value,
  and FAN$IER-style sensitivity cases.
- Typer CLI: `db`, `curve`, `product`, and `econ` commands with JSON output.
- FastAPI service and Pydantic response envelopes.
- Server-rendered FRESH-style catalog, curve, product, and economics UI.
- Deterministic assistant tools with provenance-first prompt guidance.
- Optional FEMIC adapter with package-version and data-manifest provenance.

## What this is not

- A claim that UBC-FRESH invented TIPSY, FAN$IER, or FEMIC.
- A byte-for-byte reimplementation of TASS.
- A substitute for measured BC log grades or mill-specific recovery.
- A place to commit raw government data tables, credentials, or personal paths.
- A validated FAN$IER replacement.

## Install

From a source checkout:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[api,parquet]"
python scripts/dashboard.py
fresh-tipsy --help
```

Extras:

- `api`: FastAPI, Jinja2, and uvicorn for the HTTP API and web UI.
- `parquet`: PyArrow for Parquet normalization and `db extract`.
- The minimal install supports parsing, catalog, curve, product, and economics
  commands that do not need Parquet or the API.

Download the wheel or sdist from the 0.1.0 GitHub release. Build evidence is in
[`notes/reference/package-build.md`](notes/reference/package-build.md).

## Quick start

Set the local source roots:

```bash
export TIPSY_INSTALL="/path/to/tipsy"
export TIPSY_DATABASE="$TIPSY_INSTALL/Database"
export FRESH_TIPSY_CACHE="/path/to/fresh-tipsy-cache"
```

Extract a catalog from a local licensed install:

```bash
fresh-tipsy db extract --source "$TIPSY_INSTALL" --out "$FRESH_TIPSY_CACHE"
fresh-tipsy db validate --catalog "$FRESH_TIPSY_CACHE/manifest.json" --source "$TIPSY_INSTALL"
```

Query growth, products, and economics:

```bash
fresh-tipsy curve query --catalog "$FRESH_TIPSY_CACHE/manifest.json" \
  --source "$TIPSY_INSTALL" --species PLI --site-index 20 --age 80 --pnc N --json

fresh-tipsy product recover --catalog "$FRESH_TIPSY_CACHE/manifest.json" \
  --source "$TIPSY_INSTALL" --species PLI --site-index 20 --age 80 --pnc N --json

fresh-tipsy econ run --catalog "$FRESH_TIPSY_CACHE/manifest.json" \
  --source "$TIPSY_INSTALL" --scenario scenario.json --json
```

The scenario schema and exit codes are in
[`notes/reference/cli.md`](notes/reference/cli.md). The API and web UI are in
[`notes/reference/api.md`](notes/reference/api.md) and
[`notes/reference/web.md`](notes/reference/web.md).

## Validation and evidence

- Four-species TIPSY golden regression: PLI, FDC, AT, and FDI exact ages plus
  product mass balance. See
  [`notes/reference/release-validation.md`](notes/reference/release-validation.md).
- Hand-checked economics case: NPV 335.543289 CAD/ha and site value 546.081251
  CAD/ha for the documented inputs. See
  [`notes/reference/economics.md`](notes/reference/economics.md).
- Cross-interface parity for CLI, API, web, and assistant tools.
- 376 tests passed and 13 skipped at the last preparation run; combined branch
  coverage 95.5%.
- Real-source tests skip when `TIPSY_DATABASE` is unset; a skip is not a pass.

## Known gaps

The release is deliberately explicit about missing evidence:

- TIPSY custom runtime output is unavailable under Wine.
- FAN$IER price, cost, product-suite, and NPV tables are unparsed.
- FEMIC TSR output is not captured.
- Product aggregate totals are not stored in `.taf`; aggregate checks are
  derived, with an independent #2 & Better-to-graded cross-check.
- Residue totals are absent.
- Carbon conversion is unavailable.
- No measured BC field grade or mill-specific recovery is claimed.
- FEMIC adapter call and dependency are prepared but not applied to the FEMIC
  repository.
- Wheel/sdist are prepared but not published.

See [`notes/reference/known-gaps.md`](notes/reference/known-gaps.md) for the full
list and limits.

## Citation

Cite the package, the source model, and the specific table path and SHA-256.
Raw data is not relicensed by this package.

- [`CITATION.cff`](CITATION.cff)
- [`notes/reference/citation.md`](notes/reference/citation.md)
- [`notes/reference/source-inventory.md`](notes/reference/source-inventory.md)

## Release notes

- [`RELEASE_NOTES.md`](RELEASE_NOTES.md)
- [`notes/reference/release-assets.md`](notes/reference/release-assets.md)
- [`notes/reference/release-assets.csv`](notes/reference/release-assets.csv)

## Repository map

| Path | Purpose |
| --- | --- |
| `AGENTS.md` | Operating contract for coding agents |
| `HANDOFF.md` | First-read handoff note for a new session agent |
| `ROADMAP.md` | Plan of record and issue tracker map |
| `CHANGE_LOG.md` | Dated narrative of changes |
| `RELEASE_NOTES.md` | 0.1.0 release notes and known gaps |
| `notes/plan/` | Program, data, architecture, and validation plans |
| `notes/reference/` | Source inventory, schemas, validation, and release facts |
| `notes/adr/` | Accepted design decisions |
| `docs/` | Sphinx RTFM surface |
| `scripts/check_workflow.py` | Workflow validator |
| `scripts/check_release_assets.py` | Release asset and checksum validator |
| `tests/` | pytest suite, including interface and release checks |

## License and attribution

Code is MIT licensed. Data tables and model outputs retain their original BC
government attribution. Cite the source model and table, not only this package.
No source table, normalized asset, or model output is relicensed here.

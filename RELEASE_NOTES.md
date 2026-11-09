# fresh-tipsy 0.1.0

Release date: 2026-11-09
Status: released 2026-11-09

`fresh-tipsy` is a provenance-first Python interoperability layer for BC TIPSY
and FAN$IER data tables. This release is a reimplementation and query layer; it
is not a TASS rewrite and does not claim authorship of the BC models or data.

## Included

- `.tab`/`.taf` parsers, provenance manifests, catalog, and normalization.
- Typed growth queries over precomputed TASS/TIPSY tables with interpolation,
  metrics, and source provenance.
- Product recovery for lumber, residues, log grades, graded/degraded lumber, and
  industrial logs, with mass-balance checks.
- Explicit-input product economics: prices, costs, NPV, Faustmann site value,
  and FAN$IER-style sensitivity cases.
- Typer CLI: `db`, `curve`, `product`, and `econ` commands with JSON output.
- FastAPI service and Pydantic response envelopes.
- Server-rendered FRESH-style catalog, curve, product, and economics UI.
- Deterministic assistant tools and provenance-first prompt guidance.
- Optional FEMIC adapter with package-version and data-manifest provenance.
- Wheel, sdist, package-data checks, release-asset validation, and a checksummed
  release asset register.

## Source versions

- TIPSY 4.5, source build `v3.01.13W (Feb 2017 - Jul 2021)`.
- Database: `Ministry Standard Database, February 2022`.
- FAN$IER executable and sample project are located; no price, cost, or NPV
  table is parsed or redistributed.
- FEMIC TSR output is not captured.
- No measured BC field grade is included.

## Evidence labels

```text
source_table      direct source table value
model_output      TASS/SYLVER product or grade model output
reimplemented     documented formula or derived value
validated_against matches a named reference within tolerance
experimental      documented but not fully validated
unavailable       no source, runtime, or golden output
```

Economics results are `reimplemented` and unvalidated against FAN$IER. Product
grade values are `model_output`, never measured field grades.

## Install

Download the wheel or sdist from the 0.1.0 GitHub release:

```bash
pip install ./fresh_tipsy-0.1.0-py3-none-any.whl
pip install fastapi uvicorn jinja2   # API and web UI
pip install pyarrow                  # Parquet normalization and db extract
```

The minimal install includes the CLI's core `db validate`/`catalog` and curve,
product, and economics commands. `db extract` writes Parquet and requires the
`parquet` extra.

## Verification at preparation

- 376 tests passed and 13 skipped without source roots.
- Combined branch coverage 95.5%.
- Four-species TIPSY golden regression passes when `TIPSY_DATABASE` is set.
- Wheel and sdist build and install in an isolated environment.
- Web, API, CLI, and assistant parity tests pass.
- No raw TIPSY tables or normalized assets are redistributed.

## Known gaps

See [`notes/reference/known-gaps.md`](notes/reference/known-gaps.md). The main
gaps are the TIPSY custom runtime, unparsed FAN$IER tables, FEMIC TSR, product
aggregate source totals, residue totals, carbon conversion, and the unpublished
release assets.

## Citation

See [`notes/reference/citation.md`](notes/reference/citation.md) and
[`CITATION.cff`](CITATION.cff). Cite `fresh-tipsy`, the TIPSY/FAN$IER source
models, and the specific source table path and SHA-256. Raw data is not
relicensed by this package.

## Release action

Published as tag `v0.1.0` on 2026-11-09. Raw and normalized TIPSY assets remain
withheld.

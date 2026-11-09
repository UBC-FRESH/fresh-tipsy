# fresh-tipsy program plan

Date: 2026-11-09
Status: planning baseline
Owner: UBC-FRESH

## Mission

Make BC's TIPSY and FAN$IER data and model outputs usable from Python, with
explicit provenance and tests, so public research and UBC-FRESH tools can query
growth, product recovery, and forest economics without a GUI boundary.

`fresh-tipsy` is an interoperability and reimplementation layer. It does not
claim that UBC-FRESH created TIPSY, FAN$IER, TASS, or the underlying BC data.

## Users

- UBC-FRESH researchers who need growth, product, or economics inputs in Python.
- FEMIC and related tools that need a stable growth/product/economics package.
- Public users who need to inspect or query TIPSY/FAN$IER tables without the
  Windows UI.
- Reviewers who need to see the source and validation for every published value.

## Scope

In scope:

1. Extract every accessible TIPSY database table into a sane, documented format.
2. Build a typed catalog with source metadata and checksums.
3. Query the precomputed TASS/TIPSY yield surfaces by species, site index, PNC,
   stock height, and age.
4. Expose TIPSY product columns: lumber grade × dimension, log grades,
   industrial logs, and residues.
5. Reimplement documented FAN$IER price, cost, NPV, and sensitivity logic.
6. Provide a Python API, Typer CLI, FastAPI service, FRESH-style web UI, and
   bounded LLM assistant.
7. Package `fresh-tipsy` so FEMIC and other UBC-FRESH tools can depend on it.

Out of scope:

- Reimplementing TASS growth physics from first principles.
- Byte-for-byte TIPSY or FAN$IER parity in the first release.
- Assigning measured BC log grades from model output.
- Committing raw government databases or large data assets.
- Paid data acquisition, field campaigns, or new remote-sensing purchases.

## Product shape

```text
fresh-tipsy/
  raw source tables        (external, not committed)
        ↓
  parser + provenance      (committed code)
        ↓
  normalized assets        (release artifacts + manifest)
        ↓
  catalog / growth query
        ↓
  product recovery / economics
        ↓
  CLI / API / web / assistant
        ↓
  FEMIC dependency
```

## Phase shape

| Phase | Outcome |
| --- | --- |
| P0 | Attribution, license, citation, agent contract |
| P1 | Source inventory and provenance contract |
| P2 | `.tab`/`.taf` extraction, catalog, normalized assets |
| P3 | Growth query engine over precomputed tables |
| P4 | Product recovery and FAN$IER-style economics |
| P5 | CLI, API, web UI, and assistant tools |
| P6 | Golden validation, packaging, and FEMIC integration |

## Evidence levels

Every output carries one of:

```text
source_table          directly read from a TIPSY/FAN$IER table
model_output          produced by a TIPSY/FAN$IER run
reimplemented         produced by fresh-tipsy code
validated_against     matches a named golden output within tolerance
experimental          documented but not yet fully validated
```

No output is published without a source and an evidence level.

## Main risks

- The TIPSY .NET runtime may fail on a given host. Table extraction does not
  depend on the runtime; product-output extraction does.
- FAN$IER may be a separate install or may not expose every internal table.
- TIPSY product columns are runtime outputs, not fields in the `.tab`/`.taf`
  growth tables.
- The filename grammar and some fixed-width fields need confirmation against
  headers and known tables.
- Full FAN$IER parity will require golden outputs and documented assumptions.

## Definition of done for the first public release

- The catalog covers all accessible `.tab` and `.taf` tables.
- A clean environment can install the package and fetch the data manifest.
- A user can query growth, product mix, and economics through Python and CLI.
- Golden tests compare a representative set of queries to TIPSY/FEMIC outputs.
- FEMIC can depend on the package and call at least one documented query.
- Every artifact cites its BC source and carries an evidence level.

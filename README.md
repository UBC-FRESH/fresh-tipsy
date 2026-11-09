# fresh-tipsy

A public, tested Python package for reading TIPSY and FAN$IER data tables,
exposing growth, product-recovery, and economics workflows, and preserving the
provenance of every value.

`fresh-tipsy` is a reimplementation and interoperability layer. It does not
claim authorship of TIPSY, FAN$IER, TASS, or BC government data. It exists so
those models and tables can be queried from Python, tested in the open, and
used by tools such as FEMIC without a GUI boundary.

Repository: <https://github.com/UBC-FRESH/fresh-tipsy>

## Status

Phase 0 (bootstrap and attribution) is planned. `ROADMAP.md` lists the phases,
and GitHub issues carry the live status. The first working milestone is the
table extraction and catalog layer, not a TASS rewrite.

## What this is

- A catalog and parser for the TIPSY database tables.
- A Python query engine over precomputed TASS/TIPSY yield surfaces.
- A documented product-recovery and FAN$IER-style economics layer.
- A Typer CLI, typed API, FRESH-style web UI, and bounded LLM assistant.
- A package that FEMIC and other UBC-FRESH tools can depend on.

## What this is not

- A claim that UBC-FRESH invented TIPSY or FAN$IER.
- A byte-for-byte reimplementation of TASS.
- A substitute for measured BC log grades.
- A place to commit raw government data tables or credentials.

## Source and attribution

This project uses public BC government models and tables. Every extracted or
derived asset must record:

```text
source
source version
source file
source SHA256
extraction date
citation
```

The original source remains the BC government's work. Reimplemented logic is
labelled `reimplemented` and validated against model outputs where possible.

## Plan

Read these in order:

1. [`notes/plan/0001-program-plan.md`](notes/plan/0001-program-plan.md)
2. [`notes/plan/0002-data-provenance.md`](notes/plan/0002-data-provenance.md)
3. [`notes/plan/0003-architecture.md`](notes/plan/0003-architecture.md)
4. [`notes/plan/0004-validation-release.md`](notes/plan/0004-validation-release.md)
5. [`notes/reference/tipsy-inventory.md`](notes/reference/tipsy-inventory.md)

## Quick start

This seed is a planning repository. The Python package and data workflows land
in Phase 2. Until then, the workflow gates are:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python scripts/dashboard.py
```

## Repository map

| Path | Purpose |
| --- | --- |
| `AGENTS.md` | Operating contract for coding agents |
| `ROADMAP.md` | Plan of record and issue tracker map |
| `CHANGE_LOG.md` | Dated narrative of changes |
| `notes/plan/` | Detailed program, data, architecture, and validation plans |
| `notes/reference/` | Source inventory and provenance facts |
| `notes/adr/` | Accepted design decisions |
| `docs/` | Sphinx RTFM surface |
| `scripts/check_workflow.py` | Workflow validator |
| `tests/` | pytest suite, including planning-surface checks |

## License and citation

Code is MIT licensed. Data tables and model outputs retain their original BC
government attribution. Cite the source model and table, not only this package.

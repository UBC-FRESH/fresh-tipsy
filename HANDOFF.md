# Handoff: fresh-tipsy

Date: 2026-11-09
Repository: <https://github.com/UBC-FRESH/fresh-tipsy>
Branch: `main`
Status: seed and detailed planning complete; no Phase 0 issue or phase branch yet.

This note is the first thing a new session agent should read after `AGENTS.md`.

## What this project is

`fresh-tipsy` is a public Python interoperability layer for BC TIPSY and FAN$IER
data tables. It will:

- extract TIPSY `.tab` and `.taf` database tables;
- expose a typed catalog and growth query engine over the precomputed TASS
  yield surfaces;
- expose TIPSY product columns and documented FAN$IER-style economics;
- provide a Typer CLI, FastAPI service, FRESH-style web UI, and bounded LLM
  assistant;
- become an optional package dependency for FEMIC.

It is **not** a claim that UBC-FRESH invented TIPSY or FAN$IER, and it is not a
TASS rewrite.

## Read in this order

1. `AGENTS.md` — operating contract and quality gates.
2. `ROADMAP.md` — phases P0–P6 and the detailed plan.
3. `notes/plan/0001-program-plan.md` — mission, scope, evidence levels.
4. `notes/plan/0002-data-provenance.md` — source/manifest/citation contract.
5. `notes/plan/0003-architecture.md` — package, CLI, API, web, assistant.
6. `notes/plan/0004-validation-release.md` — golden tests and release gates.
7. `notes/reference/tipsy-inventory.md` — observed TIPSY tables and runtime.
8. `notes/reference/fansier-scope.md` — FAN$IER scope and gaps.
9. `notes/adr/` — accepted design decisions.

If present, also read the untracked local file:

```text
notes/local/README.md
```

It contains host-specific TIPSY install paths and the current runtime status.
It is intentionally ignored by Git.

## Current baseline

- The repo was seeded from `UBC-FRESH/ubc-fresh-dev-workflow`.
- The dashboard is green: lint, format, mypy, tests, validator, docs.
- TIPSY 4.5 is installed locally and its `Database/` directory contains
  96 `.tab` and 96 `.taf` files.
- `.tab` and `.taf` are plain ASCII; raw tables are not committed.
- TIPSY product columns are runtime outputs, not columns in the growth tables.
- The local TIPSY .NET 4.8 runtime currently fails under Wine. Table extraction
  does not depend on it; product-output extraction does.
- No FAN$IER executable has been found yet in the same local tree.

## First milestone

Do **not** start with TASS, product recovery, or the web UI.

Start with P0 → P1 → P2:

1. Create the Phase 0 parent issue and activate P0 in `ROADMAP.md`.
2. Create `feature/p0-bootstrap`.
3. Finish the attribution/bootstrap checks.
4. Move to P1: source inventory and provenance contract.
5. Move to P2: `.tab`/`.taf` parsers, catalog, normalized assets, CLI.

The first real deliverable is:

```text
fresh-tipsy db extract
fresh-tipsy db validate
fresh-tipsy db catalog
```

plus a manifest, tiny fixtures, and tests.

## Non-negotiable rules

- Cite BC TIPSY/FAN$IER and the source table on every published value.
- Do not commit raw government databases or large normalized assets.
- Do not reimplement TASS physics.
- Do not invent product coefficients or grade assignments.
- Label reimplemented logic `reimplemented`; label model output `model_output`.
- Every CLI/API/web/assistant answer must expose provenance.
- A failed runtime is recorded as a failed run, not filled with guessed values.
- The assistant is additive; the UI must work without it.

## Commands

```bash
cd /path/to/fresh-tipsy
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python scripts/dashboard.py
```

The dashboard must be green before every commit.

## Suggested first commit sequence

```text
P0.1 activate phase 0 and create bootstrap issue
P0.2 verify attribution, citation, and public-safety rules
P1.1 inventory TIPSY source tables and output schemas
P1.2 freeze the provenance manifest schema
P2.1 implement the .tab parser
P2.2 implement the .taf parser
P2.3 build the catalog and CLI
```

## Handoff state

- Local repo: seeded and committed.
- Remote: private `UBC-FRESH/fresh-tipsy`, `main` pushed.
- Phase 0: not yet activated; no parent issue or child issues.
- Python package: not scaffolded yet; that is Phase 2 work after the provenance
  contract.
- Data assets: not committed; extraction starts in Phase 2.

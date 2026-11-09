# fresh-tipsy Roadmap

This roadmap is the plan of record and the issue tracker map for `fresh-tipsy`.
Keep it in step with the GitHub issues, `CHANGE_LOG.md`, and `notes/`.
`scripts/check_workflow.py` parses the phase headers, status lines, and
checkboxes below, so keep their format.

Every phase starts as `planned` with `Parent issue: TBD`. Activate a phase only
after its parent issue exists and the maintainer approves it.

## Issue Tracker Map

| Phase | Parent issue | Branch | Status |
| --- | --- | --- | --- |
| P0 Bootstrap and attribution | #1 | `feature/p0-bootstrap` | complete |
| P1 Source inventory and provenance | #3 | `feature/p1-source-inventory` | pr-open |
| P2 Table extraction and catalog | TBD | `feature/p2-table-extraction` | planned |
| P3 Growth query engine | TBD | `feature/p3-growth-engine` | planned |
| P4 Product recovery and economics | TBD | `feature/p4-product-economics` | planned |
| P5 CLI, API, web, and agent | TBD | `feature/p5-interfaces` | planned |
| P6 Validation, packaging, and femic integration | TBD | `feature/p6-release-integration` | planned |

## Lifecycle Map

| Stage | Phases | Exit criteria |
| --- | --- | --- |
| Bootstrap and scope | P0, P1 | Attribution, source inventory, and provenance contract recorded |
| Build | P2, P3, P4 | Tables, growth queries, and product/economics layers pass their gates |
| Interfaces | P5 | Typed API, Typer CLI, FRESH-style web UI, and LLM tools pass tests |
| Verify and release | P6 | Golden checks, package build, release assets, and `femic` integration evidence |

## Conventions

- A phase is `P<n>`. A task is `P<n>.<m>`. A subtask is a checklist item inside
  the task's issue body. Three levels at most.
- Status values are `planned`, `active`, `pr-open`, `complete`, and `deferred`.
- A phase becomes `complete` only after its pull request merges to `main` and its
  parent issue closes.
- Every published artifact carries source, version, path, SHA256, and citation.
- `fresh-tipsy` is a reimplementation and interoperability layer. It does not
  claim authorship of TIPSY, FAN$IER, TASS, or BC government data.

## Phase 0: Bootstrap and attribution

Parent issue: #1
Branch: `feature/p0-bootstrap`
Status: complete

Goal: make the repository's public purpose, attribution, and agent contract
unambiguous before code lands.

- [x] P0.1 Adapt `README.md`, `AGENTS.md`, `CITATION.cff`, and `LICENSE`
- [x] P0.2 Add the source-attribution and no-authorship rules to the docs
- [x] P0.3 Confirm the workflow validator, tests, and docs build pass
- [x] P0.4 Create the GitHub repository and Phase 0 parent issue

Acceptance criteria:

- A reader can tell what `fresh-tipsy` is, what it is not, and which BC sources
  it depends on.
- The seed's validator and docs gates are green.
- Attribution language appears in `README.md`, `AGENTS.md`, and `CITATION.cff`.

## Phase 1: Source inventory and provenance

Parent issue: #3
Branch: `feature/p1-source-inventory`
Status: pr-open

Goal: locate every source table and output schema, then freeze the provenance
contract before extraction begins.

- [x] P1.1 Inventory TIPSY and FAN$IER installs, databases, reports, and samples (#4)
- [x] P1.2 Decode `.tab` and `.taf` grammar, filename fields, and header metadata (#5)
- [x] P1.3 Map `OutputColumns.txt`, report templates, and output columns to tables (#6)
- [x] P1.4 Write the data-provenance contract and source-citation manifest (#7)
- [x] P1.5 Capture tiny fixtures and a golden output inventory (#8)

Acceptance criteria:

- Every source file has a stable identifier, source version, path, and SHA256.
- The `.tab` and `.taf` parsers have a documented grammar and field-count rule.
- Product, lumber, residue, log-grade, and economics columns are classified.
- No raw government table is committed; only fixtures and manifests are tracked.

## Phase 2: Table extraction and catalog

Parent issue: TBD
Branch: `feature/p2-table-extraction`
Status: planned

Goal: convert every TIPSY database table to a normalized, validated public
asset and make it discoverable.

- [ ] P2.1 Implement the `.tab` parser and metadata inference
- [ ] P2.2 Implement the `.taf` parser and fixed-width/tab-delimited handling
- [ ] P2.3 Implement the table catalog and search index
- [ ] P2.4 Write normalized Parquet/CSV plus a checksum manifest
- [ ] P2.5 Add `fresh-tipsy db extract`, `validate`, and `catalog` CLI commands
- [ ] P2.6 Add parser, schema, and catalog tests

Acceptance criteria:

- Every table round-trips through raw, normalized, and manifest forms.
- Field counts, age monotonicity, site-index ranges, and duplicate keys are
  validated.
- The catalog exposes species, site index, PNC, stock height, source version,
  row count, and columns.
- A user can browse and download tables without reading TIPSY documentation.

## Phase 3: Growth query engine

Parent issue: TBD
Branch: `feature/p3-growth-engine`
Status: planned

Goal: query the extracted TASS/TIPSY yield surfaces with a stable Python API.

- [ ] P3.1 Implement species/site-index/PNC/stock-height table selection
- [ ] P3.2 Implement age interpolation and scenario extraction
- [ ] P3.3 Expose volume, height, DBH, density, biomass, and carbon queries
- [ ] P3.4 Compare queries against TIPSY outputs and FEMIC TSR curves
- [ ] P3.5 Add property and regression tests for monotonicity and interpolation

Acceptance criteria:

- A query returns a typed, documented result with provenance.
- Query behavior matches golden TIPSY/FEMIC outputs within a stated tolerance.
- Unsupported species/site combinations fail explicitly, not by extrapolation.
- The engine never claims to reimplement TASS physics.

## Phase 4: Product recovery and economics

Parent issue: TBD
Branch: `feature/p4-product-economics`
Status: planned

Goal: expose TIPSY product columns, residue categories, and FAN$IER-style
economics through a documented reimplementation.

- [ ] P4.1 Map TIPSY lumber, residue, log-grade, and industrial-log columns
- [ ] P4.2 Capture or extract golden product outputs from TIPSY/FAN$IER
- [ ] P4.3 Implement product recovery with mass-balance checks
- [ ] P4.4 Implement FAN$IER-style prices, costs, NPV, and sensitivity
- [ ] P4.5 Add product/economics regression and boundary tests

Acceptance criteria:

- Lumber grades and dimensions sum to the reported lumber total.
- Residue categories reconcile with the source total where the source provides
  one.
- Product and economics outputs carry `source`, `model`, `evidence`, and
  `validation` labels.
- Grade output is labelled as model output, never as a measured BC log grade.

## Phase 5: CLI, API, web, and agent

Parent issue: TBD
Branch: `feature/p5-interfaces`
Status: planned

Goal: make the package usable by people and agents through a typed API, CLI,
FRESH-style web UI, and bounded assistant tools.

- [ ] P5.1 Build the Typer CLI and command contracts
- [ ] P5.2 Build the FastAPI service and typed response models
- [ ] P5.3 Build the FRESH-style table, curve, product, and economics UI
- [ ] P5.4 Add LLM tools for catalog search, curve query, provenance, and economics
- [ ] P5.5 Add API, CLI, UI, and assistant tests

Acceptance criteria:

- Every web/assistant answer exposes its source table and query inputs.
- The assistant cannot invent a table or omit provenance.
- CLI and API share the same typed service layer.
- The UI works without an LLM; the assistant is additive.

## Phase 6: Validation, packaging, and femic integration

Parent issue: TBD
Branch: `feature/p6-release-integration`
Status: planned

Goal: prove the package, publish it, and make it a usable dependency for FEMIC.

- [ ] P6.1 Run golden regression against TIPSY/FEMIC outputs
- [ ] P6.2 Build and test the Python package and data manifest
- [ ] P6.3 Publish release assets and a stable data manifest
- [ ] P6.4 Add the FEMIC dependency and back-link documentation
- [ ] P6.5 Write release notes, known gaps, and citation instructions

Acceptance criteria:

- A clean environment installs the package and downloads/uses the data assets.
- FEMIC can import `fresh_tipsy` and call a documented growth/product query.
- Golden checks and mass balances pass; known gaps are explicit.
- Release notes cite TIPSY, FAN$IER, and all source tables.

## Detailed Next Steps Notes

1. Create the GitHub repository and the Phase 0 parent issue. This needs
   maintainer approval.
2. Activate Phase 0 by setting its parent issue number and its status to
   `active`, here and in the tracker map.
3. Read `notes/plan/0001-program-plan.md` before opening any code task.
4. Read `notes/reference/tipsy-inventory.md` before touching table formats.
5. Do not implement Phase 3 or Phase 4 until Phase 1's provenance contract and
   Phase 2's parser tests are green.

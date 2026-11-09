# Phase close-out report: P2 Table extraction and catalog

Phase: P2 Table extraction and catalog
Parent issue: #10
Pull request: #17, `feature/p2-table-extraction` into `main`
Evidence head: `e39e711`, the head that the gates and CI runs below cover
Report commit: the commit that adds this report. Its CI run is posted on the pull request.
Date: 2026-11-09
Status: queued for approval. Not merged.

## Recommendation

Approve these actions. The agent carries them out in this order, and reads back each result.

1. Squash-merge pull request #17, and delete the branch `feature/p2-table-extraction`.
2. Close parent issue #10 with a closeout comment that cites the merge commit.
3. Launch P3: create its branch `feature/p3-growth-engine`, set the phase statuses in `ROADMAP.md`, create the P3.1–P3.5 child issues as sub-issues, and start P3.1.

Settings changes, each with its exact command. Each one runs only after its own approval.

- Create the labels that the issue templates expect:

```bash
gh label create phase --repo UBC-FRESH/fresh-tipsy --description "Phase parent issue" --color 0E8A16
gh label create task --repo UBC-FRESH/fresh-tipsy --description "Child task issue" --color 1D76DB
```

No repository visibility, branch-protection, tag, release, or external-account change is part of this close-out.

## 1. Objectives and acceptance

| Criterion | Evidence | Status |
| --- | --- | --- |
| Every table round-trips through raw, normalized, and manifest forms | Full run: 96 pairs, 192 source entries, 384 normalized assets; all 192 source tables re-normalized and round-tripped against their CSV/Parquet artifacts | met |
| Field counts, age monotonicity, site-index ranges, and duplicate keys are validated | 22/151 field enforcement, 96/96 structural pair matches, 12 age-grid differences recorded, manifest duplicate-ID checks, site-range checks | met with the age-grid caveat below |
| The catalog exposes species, site index, PNC, stock height, source version, row count, and columns | `TableCatalog` filters and entry fields; synthetic, manifest-example, and real `pli0530N00` tests | met |
| A user can browse and download tables without reading TIPSY documentation | `db catalog`, `db extract`, and `db validate` with `--json`; normalized artifacts and a checksum manifest | met |
| No raw or normalized data is committed | Only synthetic `.tab`/`.taf` fixtures are tracked; release assets are written to an output directory | met |

Full-run evidence: 96 pairs, 576 manifest assets, `db validate` returned zero errors, and all 192 source tables round-tripped to both CSV and Parquet. The 88 MB temporary output stays outside the repository.

Age-grid caveat: 12 `.tab`/`.taf` pairs have different age sequences even though headers, run counts, and row counts match. The manifest records a `taf-tab-age-grid-mismatch` gap; P3 must use each table's own age grid.

## 2. Workflow compliance

- Parent issue before the branch: issue #10 created 2026-11-09T03:18:27Z; branch launch commit `a0e63a7` at 2026-11-09T03:20:08Z; pull request #17 opened 2026-11-09T06:21:23Z.
- Branch from `main`: merge base `d6d5967`.
- Commit messages that start with task IDs: `a0e63a7` (P2.1), `b7ece10` (P2.1), `eb58a6e` (P2.2), `83e73c7` (P2.3), `f8d035a` (P2.4), `9779e5d` (P2.5), `965274e` (P2.6), `e39e711` (P2.6). The report commit starts with `P2.6`.
- Gates for each commit: section 3.
- Roadmap and changelog in step: every task commit updates `ROADMAP.md` and `CHANGE_LOG.md`; the report commit sets P2 to `pr-open`.
- Child issues closed with closeout evidence: #11, #12, #13, #14, #15, and #16.
- Approval gates: the maintainer approved the phase launch and each task through the session instructions. No settings, visibility, tag, release, or external-account change was made.

## 3. Gate evidence

| Commit | Gates run | Result |
| --- | --- | --- |
| `a0e63a7` | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |
| `b7ece10` | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |
| `eb58a6e` | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |
| `83e73c7` | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |
| `f8d035a` | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |
| `9779e5d` | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |
| `965274e` | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |
| `e39e711` | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |
| report commit | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |

Additional P2 checks:

- Test suite: 253 passed, 5 environment-dependent skipped.
- Combined branch coverage: 97.57% against the 95% gate.
- Full extraction: 96 pairs, 576 assets, zero validation errors.
- Full round trip: 192/192 source tables verified against both normalized formats.
- Package wheel: includes the CLI entry point, schema, and column-map data.
- Manifest schema/example/package copies: synchronized and validated.

## 4. CI evidence

| Run ID | Head commit | Conclusion | Notes |
| --- | --- | --- | --- |
| 42572534329 | `965274e` | failure | Mypy could not find `jsonschema` stubs in CI. Fixed by adding `types-jsonschema` in `e39e711`. |
| 42572690575 | `e39e711` | success | Quality gates, Green dashboard summary, and Pre-commit parity all passed. |
| posted on the pull request | report commit | pending at writing | The report commit triggers a fresh run; its result is posted on PR #17. |

## 5. Deviations

| Deviation | Cause | Remedy |
| --- | --- | --- |
| CI failed first on `965274e` | The local environment had usable `jsonschema` typing; CI did not | Added `types-jsonschema` in `e39e711`; rerun succeeded |
| 12 pairs have different `.tab`/`.taf` age grids | The source database uses different age sequences across formats | Recorded in the grammar note and as a manifest gap; P3 uses each table's own grid |
| Coverage gate changed from `scripts/` only to `scripts/` plus `src/fresh_tipsy/` | P2 added the package and P2.6 extended the gate | Recorded in the changelog; combined coverage is 97.57% |
| Manifest schema moved from 1.1.0 to 1.2.0 | P2.4 added `artifact` and `source_asset_ids` for release assets | Backward-compatible addition; docs, example, and tests updated |
| The P2.6 issue cites `965274e`, but the evidence head is `e39e711` | The CI stub fix came after the task commit | Recorded here; the report cites the final evidence head |

## 6. Next phase

Phase P3, growth query engine, queries the extracted TASS/TIPSY yield surfaces with a stable Python API.

Tasks:

- P3.1 Implement species/site-index/PNC/stock-height table selection.
- P3.2 Implement age interpolation and scenario extraction.
- P3.3 Expose volume, height, DBH, density, biomass, and carbon queries.
- P3.4 Compare queries against TIPSY outputs and FEMIC TSR curves.
- P3.5 Add property and regression tests for monotonicity and interpolation.

Acceptance criteria:

- A query returns a typed, documented result with provenance.
- Query behavior matches golden TIPSY/FEMIC outputs within a stated tolerance.
- Unsupported species/site combinations fail explicitly, not by extrapolation.
- The engine never claims to reimplement TASS physics.

Recommended defaults:

- Start with P3.1. Select the closest matching source table from the catalog and fail explicitly when no table covers the request.
- Use each table's own age grid. Do not align `.tab` and `.taf` rows; 12 pairs differ.
- Interpolate within the table's age range only. No extrapolation outside the first or last age.
- Return typed values with the source table ID, SHA-256, source path, query inputs, and evidence label.
- Keep `.taf` mortality positions 11-15 medium confidence and out of public means until confirmed.
- Use the real-source tests when `TIPSY_DATABASE` is set; synthetic fixtures otherwise.
- Create one child issue per P3 task and link it to the P3 parent issue before starting work.

## 7. Decision

- [ ] Approve as written.
- [ ] Approve with the changes stated here: <changes>.

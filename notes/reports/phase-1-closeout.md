# Phase close-out report: P1 Source inventory and provenance

Phase: P1 Source inventory and provenance
Parent issue: #3
Pull request: #9, `feature/p1-source-inventory` into `main`
Evidence head: `28ecb59`, the head that the gates and CI runs below cover
Report commit: the commit that adds this report. Its CI run is posted on the pull request.
Date: 2026-11-09
Status: queued for approval. Not merged.

## Recommendation

Approve these actions. The agent carries them out in this order, and reads back each result.

1. Squash-merge pull request #9, and delete the branch `feature/p1-source-inventory`.
2. Close parent issue #3 with a closeout comment that cites the merge commit.
3. Launch P2: create its branch `feature/p2-table-extraction`, set the phase statuses in `ROADMAP.md`, create the P2.1–P2.6 child issues as sub-issues, and start P2.1.

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
| Every source file has a stable identifier, source version, path, and SHA256 | P1.1 manifests: 192 tables, 66 non-database files, 5 FAN$IER files; 0 size or hash mismatches | met |
| The `.tab` and `.taf` parsers have a documented grammar and field-count rule | `tab-taf-grammar.md`: 22/151 fields, 0 exceptions, 96/96 pairs match | met |
| Product, lumber, residue, log-grade, and economics columns are classified | `output-columns.md`: 269 rows, 210 report references, 77 product fields plus 7 aggregates, 0 economics fields | met |
| No raw government table is committed; only fixtures and manifests | Only synthetic `.tab`/`.taf` fixtures are tracked; real candidates are checksum-only | met |
| The data-provenance contract and manifest schema are frozen | `manifest-schema.md`, validated `manifest-schema.json`, validated example, binding plan 0002 | met |
| Tiny fixtures and a golden output inventory are captured | Synthetic 22/151 fixtures, fixture tests, 6-entry golden inventory, checksum-only real sources | met with the stated redistribution limit |

Known limits:

- Redistribution terms for the raw tables are unclear, so no real `.tab`/`.taf` excerpt is committed.
- `.taf` positions 11-15 remain medium confidence; the mortality-summary aggregation is unresolved.
- FAN$IER economics, a TIPSY custom runtime output, and a FEMIC TSR output remain unavailable.

## 2. Workflow compliance

- Parent issue before the branch: issue #3 created 2026-11-09T01:37:04Z; branch launch commit `84d7b42` at 2026-11-09T01:39:10Z; pull request #9 opened 2026-11-09T02:38:36Z.
- Branch from `main`: merge base `4bb9776`.
- Commit messages that start with task IDs: `84d7b42` (P1.1), `a073234` (P1.1), `631d7ca` (P1.2), `05ed873` (P1.2), `b95f69d` (P1.3), `4baeae1` (P1.4), `28ecb59` (P1.5). The report commit starts with `P1.5`.
- Gates for each commit: section 3.
- Roadmap and changelog in step: every task commit updates `ROADMAP.md` and `CHANGE_LOG.md`; the report commit sets P1 to `pr-open`.
- Child issues closed with closeout evidence: #4, #5, #6, #7, and #8.
- Approval gates: the maintainer approved the phase launch and each task through the session instructions. No settings, visibility, tag, release, or external-account change was made.

## 3. Gate evidence

| Commit | Gates run | Result |
| --- | --- | --- |
| `84d7b42` | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |
| `a073234` | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |
| `631d7ca` | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |
| `05ed873` | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |
| `b95f69d` | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |
| `4baeae1` | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |
| `28ecb59` | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |
| report commit | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |

Additional P1 checks:

- Manifest validation: JSON Schema draft 2020-12 validates; the example manifest validates.
- Fixture tests: `tests/test_fixtures.py` passes without a TIPSY install.
- Source manifests: 192 table entries, 66 file entries, 5 FAN$IER entries; 0 size or SHA-256 mismatches.
- Column maps: 173 `.tab`/`.taf` columns; 269 `OutputColumns.txt` rows; 210 report-column references resolved.

## 4. CI evidence

| Run ID | Head commit | Conclusion | Notes |
| --- | --- | --- | --- |
| 42552069503 | `28ecb59` | success | Quality gates, Green dashboard summary, and Pre-commit parity all passed. |
| posted on the pull request | report commit | pending at writing | The report commit triggers a fresh run; its result is posted on PR #9. |

## 5. Deviations

| Deviation | Cause | Remedy |
| --- | --- | --- |
| The seed said product columns are absent from `.taf` | The P1.2/P1.3 evidence showed the `.taf` `Full` table contains 77 product/grade fields | Corrected the plan and reference notes in `b95f69d`; product fields are `model_output` |
| The P1.2 DR duplicate-block description was initially too broad | The two DR defects differ: a final block and block 9 | Corrected in `05ed873` |
| Real-source fixtures are checksum-only | The TIPSY use policy and release note do not state redistribution terms | No raw data is committed; synthetic fixtures cover parser tests; real candidates are checksum-only |
| `.taf` positions 11-15 remain medium confidence | The mortality-summary values do not behave like simple means | Recorded as a schema gap; not published as means |
| FAN$IER economics and custom runtime outputs are unavailable | No validated FAN$IER run; the TIPSY .NET runtime fails under Wine | Recorded as gaps in the manifest and golden inventory |
| The `phase` and `task` labels are missing | The seed did not create them | Creation commands are listed under Recommendation and wait for approval |

## 6. Next phase

Phase P2, table extraction and catalog, converts every TIPSY database table into a normalized, validated public asset and makes it discoverable.

Tasks:

- P2.1 Implement the `.tab` parser and metadata inference.
- P2.2 Implement the `.taf` parser and fixed-width/tab-delimited handling.
- P2.3 Implement the table catalog and search index.
- P2.4 Write normalized Parquet/CSV plus a checksum manifest.
- P2.5 Add `fresh-tipsy db extract`, `validate`, and `catalog` CLI commands.
- P2.6 Add parser, schema, and catalog tests.

Acceptance criteria:

- Every table round-trips through raw, normalized, and manifest forms.
- Field counts, age monotonicity, site-index ranges, and duplicate keys are validated.
- The catalog exposes species, site index, PNC, stock height, source version, row count, and columns.
- A user can browse and download tables without reading TIPSY documentation.

Recommended defaults:

- Start with P2.1 and use the synthetic fixtures; real-source tests skip when `TIPSY_DATABASE` is unset.
- Implement the P1.4 manifest schema and its 20 validation rules before writing normalized assets.
- Handle CRLF and LF input, multiple `[RUN,...]` blocks, treatment-boundary duplicate rows, and the 22/151 field counts.
- Keep product/grade columns `model_output`; keep the `.taf` mortality summary at medium confidence and do not publish its means until confirmed.
- Commit parsers, schemas, manifests, fixtures, and tests. Publish normalized assets as release artifacts, not repository content.
- Defer FAN$IER economics to P4; do not invent prices, costs, or discount rates.
- Create one child issue per P2 task and link it to the P2 parent issue before starting work.

## 7. Decision

- [ ] Approve as written.
- [ ] Approve with the changes stated here: <changes>.

# Phase close-out report: P0 Bootstrap and attribution

Phase: P0 Bootstrap and attribution
Parent issue: #1
Pull request: #2, `feature/p0-bootstrap` into `main`
Evidence head: `126a2a3`, the head that the gates and CI runs below cover
Report commit: the commit that adds this report. Its CI run is posted on the pull request.
Date: 2026-11-09
Status: queued for approval. Not merged.

## Recommendation

Approve these actions. The agent carries them out in this order, and reads back each result.

1. Squash-merge pull request #2, and delete the branch `feature/p0-bootstrap`.
2. Close parent issue #1 with a closeout comment that cites the merge commit.
3. Launch P1: create its branch `feature/p1-source-inventory`, set the phase statuses in `ROADMAP.md`, create the P1.1–P1.5 child issues as sub-issues, and start P1.1.

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
| A reader can tell what `fresh-tipsy` is, what it is not, and which BC sources it depends on | `README.md` "What this is", "What this is not", and "Source and attribution"; `docs/overview.rst` "Source attribution" and "Non-goals" | met |
| The seed's validator and docs gates are green | `python scripts/dashboard.py` GREEN at `40b254a`, `d1e396f`, and `126a2a3`; CI run 42544943097 passed | met |
| Attribution language appears in `README.md`, `AGENTS.md`, and `CITATION.cff` | Present in all three; `CITATION.cff` references TIPSY and FAN$IER under the Province of British Columbia | met |

## 2. Workflow compliance

- Parent issue before the branch: issue #1 created 2026-11-09T01:10:32Z; branch commit `d1e396f` at 2026-11-09T01:11:02Z; pull request #2 opened 2026-11-09T01:19:08Z.
- Branch from `main`: merge base `40b254a`.
- Commit messages that start with task IDs: `d1e396f` (`P0.4`) and `126a2a3` (`P0.1`); the report commit starts with `P0.4`.
- Gates for each commit: section 3.
- Roadmap and changelog in step: `d1e396f` activated P0; `126a2a3` checked P0.1–P0.3 and recorded the result; the report commit sets P0 to `pr-open`.
- Child issues closed with closeout evidence: none. P0.1–P0.3 were tracked on parent issue #1 instead of separate child issues; see section 5.
- Approval gates: the maintainer approved P0 activation, the parent issue, and the branch. No settings, visibility, tag, release, or external-account change was made.

## 3. Gate evidence

| Commit | Gates run | Result |
| --- | --- | --- |
| `40b254a` | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |
| `d1e396f` | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |
| `126a2a3` | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |
| report commit | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |

## 4. CI evidence

| Run ID | Head commit | Conclusion | Notes |
| --- | --- | --- | --- |
| 42544943097 | `126a2a3` | success | Quality gates, Green dashboard summary, and Pre-commit parity all passed. |
| posted on the pull request | report commit | pending at writing | The report commit triggers a fresh run; its result is posted on PR #2. |

## 5. Deviations

| Deviation | Cause | Remedy |
| --- | --- | --- |
| No separate child issues for P0.1–P0.3 | The tasks were small and tracked on parent issue #1 | Recorded here. P1 will create one child issue per task before its work starts. |
| The `phase` and `task` labels are missing | The seed did not create them | Creation commands are listed under Recommendation and wait for approval. |
| P0.1 and P0.2 were already largely satisfied by the seed | The seed carried initial attribution text | Audited in `126a2a3`; fixed the stale README phase status and a duplicated `AGENTS.md` heading. |

## 6. Next phase

Phase P1, source inventory and provenance, locates every source table and output schema, then freezes the provenance contract before extraction begins.

Tasks:

- P1.1 Inventory TIPSY and FAN$IER installs, databases, reports, and samples.
- P1.2 Decode `.tab` and `.taf` grammar, filename fields, and header metadata.
- P1.3 Map `OutputColumns.txt`, report templates, and output columns to tables.
- P1.4 Write the data-provenance contract and source-citation manifest.
- P1.5 Capture tiny fixtures and a golden output inventory.

Acceptance criteria:

- Every source file has a stable identifier, source version, path, and SHA256.
- The `.tab` and `.taf` parsers have a documented grammar and field-count rule.
- Product, lumber, residue, log-grade, and economics columns are classified.
- No raw government table is committed; only fixtures and manifests are tracked.

Recommended defaults:

- Start with P1.1. Discover the install through `TIPSY_INSTALL` and `TIPSY_DATABASE`, hash all 192 `.tab`/`.taf` files, and record metadata without committing raw tables.
- Check `FANSIER_INSTALL`; if no install exists, record the economics source as `unavailable` rather than guessing.
- Choose the smallest representative `.tab` and `.taf` files for fixtures, and publish checksums plus reproduction commands when redistribution is unclear.
- Create one child issue per P1 task and link it to the P1 parent issue before starting work.

## 7. Decision

- [ ] Approve as written.
- [ ] Approve with the changes stated here: <changes>.

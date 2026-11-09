# Phase close-out report: P3 Growth query engine

Phase: P3 Growth query engine
Parent issue: #18
Pull request: #24, `feature/p3-growth-engine` into `main`
Evidence head: `0f5a1bc`, the head that the gates and CI runs below cover
Report commit: the commit that adds this report. Its CI run is posted on the pull request.
Date: 2026-11-09
Status: queued for approval. Not merged.

## Recommendation

Approve these actions. The agent carries them out in this order, and reads back each result.

1. Squash-merge pull request #24, and delete the branch `feature/p3-growth-engine`.
2. Close parent issue #18 with a closeout comment that cites the merge commit.
3. Launch P4: create its branch `feature/p4-product-economics`, set the phase statuses in `ROADMAP.md`, create the P4.1–P4.5 child issues as sub-issues, and start P4.1.

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
| A query returns a typed, documented result with provenance | `CurvePoint`, `MetricValue`, `TableSelection`, and `Provenance`; every result carries table ID, SHA-256, path, and citation | met |
| Query behavior matches golden TIPSY/FEMIC outputs within a stated tolerance | Exact-age PLI, FDC, AT, and FDI checks at `1e-9`; PLI midpoint interpolation at `1e-6`; FEMIC TSR unavailable | met for TIPSY; FEMIC recorded as a gap |
| Unsupported species/site combinations fail explicitly | Typed errors for species, site, PNC, stock height, version, format, scenario, age, source root, and metric | met |
| The engine never claims to reimplement TASS physics | The engine selects and interpolates precomputed TASS/TIPSY tables only; docs state the boundary | met |

Known limits:

- No redistributable FEMIC TSR output is captured.
- Carbon metrics are not exposed: no stored carbon columns or documented conversion factor.
- `.taf` mortality positions 11-15 remain medium confidence.
- The committed golden test covers PLI; the close-out run additionally checked FDC, AT, and FDI exact ages.

## 2. Workflow compliance

- Parent issue before the branch: issue #18 created 2026-11-09T06:44:47Z; branch launch commit `907bc6e` at 2026-11-09T06:45:56Z; pull request #24 opened 2026-11-09T13:11:58Z.
- Branch from `main`: merge base `55214c1`.
- Commit messages that start with task IDs: `907bc6e` (P3.1), `ceca37c` (P3.1), `7792a7a` (P3.2), `a949ae3` (P3.3), `8904cbf` (P3.4), `0f5a1bc` (P3.5). The report commit starts with `P3.5`.
- Gates for each commit: section 3.
- Roadmap and changelog in step: every task commit updates `ROADMAP.md` and `CHANGE_LOG.md`; the report commit sets P3 to `pr-open`.
- Child issues closed with closeout evidence: #19, #20, #21, #22, and #23.
- Approval gates: the maintainer approved the phase launch and each task through the session instructions. No settings, visibility, tag, release, or external-account change was made.

## 3. Gate evidence

| Commit | Gates run | Result |
| --- | --- | --- |
| `907bc6e` | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |
| `ceca37c` | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |
| `7792a7a` | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |
| `a949ae3` | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |
| `8904cbf` | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |
| `0f5a1bc` | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |
| report commit | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |

Additional P3 checks:

- Tests: 295 passed, 10 environment-dependent skips.
- Combined branch coverage: 97.58% against the 95% gate.
- `curves/` package branch coverage: 97%.
- Exact-age PLI, FDC, AT, and FDI queries matched source-table values at `1e-9`.
- PLI midpoint interpolation matched the hand-derived value at `1e-6`.
- FEMIC TSR comparison is documented as unavailable.

## 4. CI evidence

| Run ID | Head commit | Conclusion | Notes |
| --- | --- | --- | --- |
| 42623369061 | `0f5a1bc` | success | Quality gates, Green dashboard summary, and Pre-commit parity all passed. |
| posted on the pull request | report commit | pending at writing | The report commit triggers a fresh run; its result is posted on PR #24. |

## 5. Deviations

| Deviation | Cause | Remedy |
| --- | --- | --- |
| FEMIC TSR comparison is unavailable | No redistributable FEMIC output was captured | Recorded in `curve-validation.md` and `golden-outputs.md`; not treated as a pass |
| Carbon metrics are unavailable | The extracted tables store biomass but not carbon; no documented conversion factor is sourced | Recorded in `METRICS` and returned as an explicit unavailable metric |
| The `.taf` mortality summary remains medium confidence | Positions 11-15 do not behave like simple means | Kept out of public means |
| The committed golden test covers one real species | P3.4 chose a representative PLI pair | The close-out run checked FDC, AT, and FDI exact ages without committing source data |

## 6. Next phase

Phase P4, product recovery and economics, exposes TIPSY product columns, residue categories, and documented FAN$IER-style economics.

Tasks:

- P4.1 Map TIPSY lumber, residue, log-grade, and industrial-log columns.
- P4.2 Capture or extract golden product outputs from TIPSY/FAN$IER.
- P4.3 Implement product recovery with mass-balance checks.
- P4.4 Implement FAN$IER-style prices, costs, NPV, and sensitivity.
- P4.5 Add product/economics regression and boundary tests.

Acceptance criteria:

- Lumber grades and dimensions sum to the reported lumber total.
- Residue categories reconcile with the source total where the source provides one.
- Product and economics outputs carry `source`, `model`, `evidence`, and `validation` labels.
- Grade output is labelled as model output, never as a measured BC log grade.

Recommended defaults:

- Start with P4.1 and map the `.taf` product, lumber, residue, log-grade, and industrial-log columns that P1.3 already classified.
- Treat every product and grade value as `model_output`; never a measured field grade.
- Make mass balance a hard gate: product totals plus residues and losses must reconcile with the source total.
- The TIPSY runtime fails under Wine. Use the precomputed `.taf` product columns and checksum-only output candidates; record custom runtime gaps.
- FAN$IER prices and costs are not parsed. Start from public documentation and label the result `reimplemented`; do not invent a price, cost, or discount rate.
- Carbon remains unavailable until a documented factor is sourced.
- Create one child issue per P4 task and link it to the P4 parent issue before starting work.

## 7. Decision

- [ ] Approve as written.
- [ ] Approve with the changes stated here: <changes>.

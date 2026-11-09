# Phase close-out report: P4 Product recovery and economics

Phase: P4 Product recovery and economics
Parent issue: #25
Pull request: #31, `feature/p4-product-economics` into `main`
Evidence head: `356a482`, the head that the gates and CI runs below cover
Report commit: the commit that adds this report. Its CI run is posted on the pull request.
Date: 2026-11-09
Status: queued for approval. Not merged.

## Recommendation

Approve these actions. The agent carries them out in this order, and reads back each result.

1. Squash-merge pull request #31, and delete the branch `feature/p4-product-economics`.
2. Close parent issue #25 with a closeout comment that cites the merge commit.
3. Launch P5: create its branch `feature/p5-interfaces`, set the phase statuses in `ROADMAP.md`, create the P5.1–P5.5 child issues as sub-issues, and start P5.1.

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
| Expose TIPSY product columns and grade groups with provenance | P4.1 typed all 77 `.taf` product fields in six groups; every field is `model_output` and maps to the packaged column positions; `tests/test_product_schema.py` | met |
| Lumber grades and dimensions sum to the reported lumber total | P4.3 derives the four aggregates and checks their components; the independent #2 & Better-to-graded cross-check uses stored fields; synthetic pass/fail tests and real PLI ages pass | met with a stated limit: the `.taf` source does not store the aggregate totals, so the aggregate checks are not independent |
| Log grades and residues aggregate correctly | Eight log grades and five residue components are exposed; logs reconcile; residues report `unavailable` because the source has no residue total | met for logs; residues are an explicit source gap |
| Product and economics outputs carry source, model, evidence, and validation labels | `ProductRecovery` carries table provenance and `model_output`; `EconomicResult` carries model, version, path, SHA-256, citation, `reimplemented`, and `unvalidated` | met |
| Grade output is model output, never a measured BC log grade | P4.1–P4.5 label every grade `model_output`; the docs repeat the boundary | met |
| Capture or record golden product outputs | P4.2 records four checksum-only `.taf` candidates and checks TIPSY/FAN$IER evidence; custom runtime and FAN$IER tables are recorded gaps | met with recorded gaps |
| Explicit FAN$IER-style prices, costs, NPV, and sensitivity | P4.4 implements explicit price/cost books, revenue, NPV, site value, and ten sensitivity cases; no default price or cost table is embedded | met |
| Product/economics regression and boundary tests | P4.5 covers schema, aggregation, missing dimensions, bad totals, provenance, real PLI ages, missing prices, zero quantities, unit gaps, hand-checked NPV, and sensitivity deltas | met |
| No raw data, invented coefficient, or measured-grade claim | Tests use synthetic fixtures or a local source install; no raw `.tab`/`.taf`/`.fns` asset is committed; no default price/cost is embedded | met |

Known limits:

- The `.taf` source does not store `Lumber_2_or_Better_All`, `Lumber_Graded_All`, `Lumber_Degraded_All`, or `Logs_Grade_All`; the runtime that would print them fails under Wine.
- No residue total exists, so residue reconciliation is `unavailable`.
- No FAN$IER price table, cost table, or golden output is parsed; economics is unvalidated against FAN$IER.
- Carbon remains unavailable; no documented conversion factor is sourced.
- Some `dr` tables put all graded grades in the #2 & Better aggregate; the cross-check reconciles that convention and records it in the check note.
- No FEMIC TSR output is captured.

## 2. Workflow compliance

- Parent issue before the branch: issue #25 created 2026-11-09T13:18:01Z; launch commit `32410d2` at 2026-11-09T13:18:53Z; pull request #31 opened 2026-11-09T15:54:33Z.
- Branch from `main`: merge base `a6c07ea`.
- Commit messages that start with task IDs: `32410d2` (P4.1 launch), `09a9e0b` (P4.1), `538065e` (P4.2), `64329c0` (P4.3), `ee06134` (P4.4), `356a482` (P4.5). The report commit starts with `P4`.
- Gates for each commit: section 3.
- Roadmap and changelog in step: every task commit updates `ROADMAP.md` and `CHANGE_LOG.md`; the report commit sets P4 to `pr-open`.
- Child issues closed with closeout evidence: #26, #27, #28, #29, and #30.
- Approval gates: the maintainer approved the phase launch and each task through the session instructions. No settings, visibility, tag, release, or external-account change was made.

## 3. Gate evidence

| Commit | Gates run | Result |
| --- | --- | --- |
| `32410d2` | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |
| `09a9e0b` | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |
| `538065e` | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |
| `64329c0` | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |
| `ee06134` | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |
| `356a482` | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |
| report commit | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |

Additional P4 checks:

- Tests at the evidence head: 332 passed, 12 environment-dependent skips.
- Combined branch coverage: 98.11% against the 95% gate.
- `products/` and `economics/` branch coverage: 100%.
- Real-source PLI product checks at ages 36, 55, and 91 pass every available mass-balance check.
- Product checksum candidates match their source files when `TIPSY_DATABASE` and `FANSIER_INSTALL` are set.
- A read-only scan of all 96 `.taf` tables found 65,230 reconciling #2 & Better rows, 1,586 rows with no graded breakdown, and zero mass-balance failures.
- Hand-checked economics case: 1000 CAD/ha revenue at age 10, 50 CAD/ha cost at age 0, 10% discount gives NPV 335.543289 and SV 546.081251 CAD/ha.

## 4. CI evidence

| Run ID | Head commit | Conclusion | Notes |
| --- | --- | --- | --- |
| 42649377189 | `356a482` | success | Quality gates, Green dashboard summary, and Pre-commit parity all passed. |
| posted on the pull request | report commit | pending at writing | The report commit triggers a fresh run; its result is posted on PR #31. |

## 5. Deviations

| Deviation | Cause | Remedy |
| --- | --- | --- |
| Task commits had no CI run before the pull request | The PR was opened at phase close-out after the five task commits | Local dashboards were run at every task head; PR run 42649377189 covers the evidence head |
| Product aggregate checks are derived, not independent | The source does not store product aggregate totals and the runtime is unavailable | The independent #2 & Better-to-graded cross-check is a hard gate; the limitation is documented in `product-recovery.md` |
| Residue reconciliation is unavailable | No residue total exists in the source | Recorded as an explicit `unavailable` check; no remainder is invented |
| TIPSY custom runtime capture is unavailable | The `.NET Framework 4.8` runtime fails under Wine | Recorded in `product-goldens.md`; the package uses precomputed `.taf` product columns |
| FAN$IER economics is unvalidated | Price/cost tables are unparsed and no golden output exists | Explicit inputs only, `reimplemented`/`unvalidated` labels, and recorded gaps in `economics.md` |
| Real-source product tests skip in CI | CI has no TIPSY source install | Tests skip explicitly; the close-out run used `TIPSY_DATABASE` locally and passed |

## 6. Next phase

Phase P5, CLI, API, web, and agent, makes the package usable by people and agents through a typed service layer.

Tasks:

- P5.1 Build the Typer CLI and command contracts.
- P5.2 Build the FastAPI service and typed response models.
- P5.3 Build the FRESH-style table, curve, product, and economics UI.
- P5.4 Add LLM tools for catalog search, curve query, provenance, and economics.
- P5.5 Add API, CLI, UI, and assistant tests.

Acceptance criteria:

- Every web/assistant answer exposes its source table and query inputs.
- The assistant cannot invent a table or omit provenance.
- CLI and API share the same typed service layer.
- The UI works without an LLM; the assistant is additive.

Recommended defaults:

- Start with P5.1 and put shared query, product, and economics calls behind one service layer before adding interfaces.
- Use Typer for the CLI and FastAPI for the service, matching `notes/plan/0003-architecture.md`.
- Keep the first UI server-rendered with a provenance drawer; avoid a frontend build step until a concrete need appears.
- Make assistant tools deterministic wrappers over the same service layer; the LLM adapter remains optional.
- Every interface response includes `request`, `result`, `provenance`, `evidence`, and `warnings`.
- Add child issues P5.1–P5.5 before starting work, and keep raw data out of the repository.
- Create the missing `phase` and `task` labels only with separate approval.

Open choices and defaults:

- Service response envelope: use one shared dataclass with request, result, provenance, evidence, and warnings.
- UI stack: FastAPI plus server-rendered templates and static assets; add HTMX only if interactivity needs it.
- Assistant runtime: no model dependency in core; provide tools and an optional adapter.
- Branch: `feature/p5-interfaces`.

## 7. Decision

- [ ] Approve as written.
- [ ] Approve with the changes stated here: <changes>.

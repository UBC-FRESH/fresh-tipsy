# Phase close-out report: P5 CLI, API, web, and agent

Phase: P5 CLI, API, web, and agent
Parent issue: #32
Pull request: #38, `feature/p5-interfaces` into `main`
Evidence head: `485511f`, the head that the gates and CI runs below cover
Report commit: the commit that adds this report. Its CI run is posted on the pull request.
Date: 2026-11-09
Status: queued for approval. Not merged.

## Recommendation

Approve these actions. The agent carries them out in this order, and reads back each result.

1. Squash-merge pull request #38, and delete the branch `feature/p5-interfaces`.
2. Close parent issue #32 with a closeout comment that cites the merge commit.
3. Launch P6: create its branch `feature/p6-release-integration`, set the phase statuses in `ROADMAP.md`, create the P6.1–P6.5 child issues as sub-issues, and start P6.1.

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
| Every web/assistant answer exposes its source table and query inputs | Service envelope carries `request`, `result`, `provenance`, `evidence`, and `warnings`; UI drawers repeat them; tool results use the same fields; parity tests in `tests/test_interfaces.py` | met |
| The assistant cannot invent a table or omit provenance | Tools only call the shared service; `agent/prompts.py` requires provenance and refusal; tool tests cover errors and partial comparisons | met |
| CLI and API share the same typed service layer | CLI commands `curve query`, `product recover`, and `econ run` call `fresh_tipsy.api.service`; API endpoints call the same functions; parity tests assert equal values | met |
| The UI works without an LLM; the assistant is additive | Web app imports the service and templates only; no agent or model dependency; UI tests run without a model or network | met |
| Missing data is an explicit gap, not zero | Missing prices, ambiguous prices, unit mismatches, unavailable mass balance, and not-configured routes are explicit gaps or structured errors | met |
| Interface tests cover success, errors, and provenance | CLI, API, web, assistant, and parity tests; 363 passed and 12 environment-dependent skips | met |
| No raw data or invented coefficient | Tests use synthetic fixtures or a local install; no price/cost default is embedded | met |

Known limits:

- The web economics form supports one price line and one cost line; the CLI
  and API scenario JSON support multi-line scenarios.
- No live LLM adapter, prompt-evaluation suite, or conversation persistence is
  included. The deterministic tools and prompt are the boundary.
- UI tests are route and template assertions, not browser automation.
- Real-source tests skip in CI without a TIPSY install; the local close-out run
  used the available source root.
- FAN$IER remains unparsed and unvalidated; economics stays explicit-input and
  `reimplemented`.
- No measured BC log grade or mill-specific recovery is claimed.

## 2. Workflow compliance

- Parent issue before the branch: issue #32 created 2026-11-09T16:00:18Z; launch commit `6a2b042` at 2026-11-09T16:01:50Z; pull request #38 opened 2026-11-09T17:08:38Z.
- Branch from `main`: merge base `96ea0e0`.
- Commit messages that start with task IDs: `6a2b042` (P5.1 launch), `e91eb68` (P5.1), `6496ee1` (P5.2), `cb66a24` (P5.3), `7021d52` (P5.4), `485511f` (P5.5). The report commit starts with `P5`.
- Gates for each commit: section 3.
- Roadmap and changelog in step: every task commit updates `ROADMAP.md` and `CHANGE_LOG.md`; the report commit sets P5 to `pr-open`.
- Child issues closed with closeout evidence: #33, #34, #35, #36, and #37.
- Approval gates: the maintainer approved the phase launch and each task through the session instructions. No settings, visibility, tag, release, or external-account change was made.

## 3. Gate evidence

| Commit | Gates run | Result |
| --- | --- | --- |
| `6a2b042` | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |
| `e91eb68` | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |
| `6496ee1` | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |
| `cb66a24` | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |
| `7021d52` | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |
| `485511f` | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |
| report commit | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |

Additional P5 checks:

- Tests at the evidence head: 363 passed, 12 environment-dependent skips.
- Combined branch coverage: 96.33% against the 95% gate.
- `web/` branch coverage: 100%; `api/app.py`: 97%.
- Cross-interface curve, product, and economics parity passes.
- Shared envelope keys, missing-price gaps, and error codes are asserted.
- The UI renders without an LLM or external network.
- No raw data or invented coefficient is committed.

## 4. CI evidence

| Run ID | Head commit | Conclusion | Notes |
| --- | --- | --- | --- |
| 42661720073 | `485511f` | success | Quality gates, Green dashboard summary, and Pre-commit parity all passed. |
| posted on the pull request | report commit | pending at writing | The report commit triggers a fresh run; its result is posted on PR #38. |

## 5. Deviations

| Deviation | Cause | Remedy |
| --- | --- | --- |
| Task commits had no CI run before the pull request | The PR was opened at phase close-out after the five task commits | Local dashboards were run at every task head; PR run 42661720073 covers the evidence head |
| Web economics form is single-price and single-cost | The first UI keeps the form small and server-rendered | CLI/API scenario JSON supports multi-line scenarios; documented in `web.md` |
| No live LLM adapter | The core must remain installable without a model or API key | Deterministic tools and prompt are provided; adapter is optional |
| No browser automation | Avoids a brittle browser stack and network dependency | Route and template assertions cover rendering and provenance |
| Real-source tests skip in CI | CI has no TIPSY source install | Tests skip explicitly; local close-out run used the available source root |
| Economics remains unvalidated | FAN$IER tables and golden outputs are unavailable | Explicit inputs, `reimplemented`/`unvalidated` labels, and recorded gaps |

## 6. Next phase

Phase P6, validation, packaging, and femic integration, proves the package,
publishes it, and makes it a usable dependency for FEMIC.

Tasks:

- P6.1 Run golden regression against TIPSY/FEMIC outputs.
- P6.2 Build and test the Python package and data manifest.
- P6.3 Publish release assets and a stable data manifest.
- P6.4 Add the FEMIC dependency and back-link documentation.
- P6.5 Write release notes, known gaps, and citation instructions.

Acceptance criteria:

- A clean environment installs the package and downloads/uses the data assets.
- FEMIC can import `fresh_tipsy` and call a documented growth/product query.
- Golden checks and mass balances pass; known gaps are explicit.
- Release notes cite TIPSY, FAN$IER, and all source tables.

Recommended defaults:

- Start with P6.1 and reuse the existing TIPSY exact-age and product checks.
  Record FEMIC TSR as unavailable unless a redistributable output is captured.
- Build a wheel and sdist in a clean environment; verify `fresh-tipsy --help`,
  `db validate`, the test suite, docs, and workflow validation.
- Publish the manifest and checksums, not raw source tables; keep rebuild
  instructions for locally licensed installs.
- Add FEMIC as an optional dependency and pass `fresh-tipsy` provenance through
  the adapter. Do not copy modules into FEMIC.
- Write release notes with version, source versions, evidence labels, and known
  gaps. Cite TIPSY, FAN$IER, and the source tables.
- Create child issues P6.1–P6.5 before starting work. Create the missing
  `phase` and `task` labels only with separate approval.

Open choices and defaults:

- Package version: keep `0.1.0` for the first release unless the maintainer
  selects another version.
- Release assets: manifest, checksums, normalized assets where redistribution
  permits, and rebuild instructions otherwise.
- FEMIC integration: optional `fresh-tipsy` dependency with a fixture-based
  test and explicit skip when the package is absent.
- Branch: `feature/p6-release-integration`.

## 7. Decision

- [ ] Approve as written.
- [ ] Approve with the changes stated here: <changes>.

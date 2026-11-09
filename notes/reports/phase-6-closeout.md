# Phase close-out report: P6 Validation, packaging, and FEMIC integration

Phase: P6 Validation, packaging, and FEMIC integration
Parent issue: #39
Pull request: #45, `feature/p6-release-integration` into `main`
Evidence head: `40794ae`, the head that the gates and CI runs below cover
Report commit: the commit that adds this report. Its CI run is posted on the pull request.
Date: 2026-11-09
Status: queued for approval. Not merged or published.

## Recommendation

Approve these actions. The agent carries them out in this order, and reads back each result.

1. Squash-merge pull request #45, and delete the branch `feature/p6-release-integration`.
2. Close parent issue #39 with a closeout comment that cites the merge commit.
3. Record the project as release-ready. Do not create a tag, GitHub release, upload, or FEMIC repository change without a separate approval.

Settings changes, each with its exact command. Each one runs only after its own approval.

- Create the labels that the issue templates expect:

```bash
gh label create phase --repo UBC-FRESH/fresh-tipsy --description "Phase parent issue" --color 0E8A16
gh label create task --repo UBC-FRESH/fresh-tipsy --description "Child task issue" --color 1D76DB
```

Separate release actions requiring their own approval:

- Create tag `v0.1.0` and a GitHub release with the prepared wheel, sdist, checksums, and release notes.
- Apply the FEMIC optional dependency, adapter call, test, and backlink in the FEMIC repository.
- Any external-account or repository-visibility change.

## 1. Objectives and acceptance

| Criterion | Evidence | Status |
| --- | --- | --- |
| A clean environment installs the package and uses the data manifest | P6.2 built wheel/sdist and installed the wheel in an isolated environment; `fresh-tipsy --help`, `db validate`, and an exact-age query passed; `notes/reference/package-build.md` | met |
| FEMIC can import `fresh_tipsy` and call a documented growth/product query | P6.4 adapter provides `query_growth`, `recover_products`, `run_economics`, and `asset_provenance`; tests pass; FEMIC-side dependency change remains pending separate approval | met on the fresh-tipsy side; FEMIC repository change pending |
| Golden checks and mass balances pass; known gaps are explicit | P6.1 four-species TIPSY regression and product checks; `release-validation.md`, `known-gaps.md`, and `release-assets.md` record limits | met with stated limits |
| Release notes cite TIPSY, FAN$IER, and source tables | `RELEASE_NOTES.md`, `CITATION.cff`, `citation.md`, and checksummed source-table manifests | met |
| No raw data, personal path, invented coefficient, or measured-grade claim | Tests use synthetic fixtures or local source reads; release assets withhold raw/normalized tables; no price/cost default is embedded | met |
| Release assets and stable data manifest are defined | P6.3 asset register and validator; schema 1.2.0; raw/normalized assets withheld | met, publication pending approval |

Known limits:

- No tag, GitHub release, or asset upload has been created.
- The FEMIC repository has not been modified; its worktree contains unrelated
  changes and external repository changes need separate approval.
- TIPSY custom runtime output and FEMIC TSR remain unavailable.
- FAN$IER price/cost tables remain unparsed and economics remains unvalidated.
- Product aggregate source totals and residue totals are absent.
- Carbon conversion is unavailable.
- The four-species golden set is representative, not all 96 table pairs.
- `db extract` requires the optional `parquet` extra.
- No live LLM adapter or browser automation is included.

## 2. Workflow compliance

- Parent issue before the branch: issue #39 created 2026-11-09T17:22:05Z; launch commit `69317de` at 2026-11-09T17:23:40Z; pull request #45 opened 2026-11-09T21:33:52Z.
- Branch from `main`: merge base `fa59ed0`.
- Commit messages that start with task IDs: `69317de` (P6.1 launch), `b0c0235` (P6.1), `07a9d80` (P6.2), `5f523b5` (P6.3), `524a5aa` (P6.4), `40794ae` (P6.5). The report commit starts with `P6`.
- Gates for each commit: section 3.
- Roadmap and changelog in step: every task commit updates `ROADMAP.md` and `CHANGE_LOG.md`; the report commit sets P6 to `pr-open`.
- Child issues closed with closeout evidence: #40, #41, #42, #43, and #44.
- Approval gates: the maintainer approved the phase launch and each task through the session instructions. No tag, release, upload, or external repository change was made.

## 3. Gate evidence

| Commit | Gates run | Result |
| --- | --- | --- |
| `69317de` | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |
| `b0c0235` | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |
| `07a9d80` | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |
| `5f523b5` | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |
| `524a5aa` | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |
| `40794ae` | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |
| report commit | `python scripts/dashboard.py` | GREEN: lint, format, types, tests, validator, docs |

Additional P6 checks:

- Tests at the evidence head: 376 passed, 13 environment-dependent skips.
- Combined branch coverage: 95.47% against the 95% gate.
- Four-species TIPSY golden regression passes with `TIPSY_DATABASE`.
- Wheel and sdist built; clean-install CLI, manifest validation, and curve query passed.
- Release validator passes on a checksummed wheel/sdist directory and rejects raw tables.
- FEMIC adapter tests pass for growth, products, economics, provenance, and structured errors.
- Docs build with warnings as errors; links and citations validate.
- No raw data or personal path is committed.

## 4. CI evidence

| Run ID | Head commit | Conclusion | Notes |
| --- | --- | --- | --- |
| 42703691420 | `40794ae` | success | Quality gates, Green dashboard summary, and Pre-commit parity all passed. |
| posted on the pull request | report commit | pending at writing | The report commit triggers a fresh run; its result is posted on PR #45. |

## 5. Deviations

| Deviation | Cause | Remedy |
| --- | --- | --- |
| Task commits had no CI run before the pull request | The PR was opened at phase close-out after the five task commits | Local dashboards were run at every task head; PR run 42703691420 covers the evidence head |
| FEMIC repository change is not applied | Its worktree has unrelated changes; external repository changes need separate approval | Adapter, tests, and docs are complete in fresh-tipsy; FEMIC-side change is queued as a separate approval |
| Release assets are not published | A tag, release, or upload needs separate approval | Wheel/sdist, checksums, asset register, and release notes are prepared |
| Minimal `db extract` needs PyArrow | Normalization writes Parquet by default | Documented the `parquet` extra in README, release notes, and package-build notes |
| TIPSY runtime and FEMIC TSR are unavailable | Host runtime and golden-output gaps | Recorded as `unavailable`; not counted as passes |
| FAN$IER economics is unvalidated | Price/cost tables and golden outputs are unavailable | Explicit inputs, `reimplemented`/`unvalidated` labels, and known-gaps documentation |
| Golden coverage is four species | Representative release smoke set | Recorded as a limit; full-table checks remain future work |

## 6. Next phase

There is no P7 in the roadmap. Phase 6 is the final planned phase. After merge,
the project is release-ready, with two separate approval tracks:

1. Release publication:
   - create tag `v0.1.0`;
   - create a GitHub release;
   - attach the prepared wheel, sdist, checksums, release notes, and asset
     register;
   - keep raw and normalized data withheld.
2. FEMIC adoption:
   - add the optional `fresh-tipsy>=0.1` dependency;
   - call the adapter;
   - pass provenance, package version, and manifest hash through FEMIC;
   - add the skip-safe integration test and backlink.

Recommended defaults:

- Start with the release publication after merge, because the package artifacts
  are already built and smoke-tested.
- Then apply the FEMIC adapter in a separate FEMIC branch and PR.
- Keep `0.1.0` and schema `1.2.0` unless the maintainer selects another version.
- Do not publish raw TIPSY or normalized assets without a redistribution basis.

## 7. Decision

- [ ] Approve as written.
- [ ] Approve with the changes stated here: <changes>.

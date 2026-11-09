# Change Log

Newest entries last. Each milestone gets a dated entry that matches the roadmap status and the GitHub issue comments.

## 2026-11-09

- Created fresh-tipsy from the UBC-FRESH dev workflow seed. The agent contract, roadmap, docs skeleton, and validator came from the seed. Every phase is planned, and no parent issues exist yet.
- Added the program, data/provenance, architecture, and validation/release plans under `notes/plan/`.
- Added TIPSY and FAN$IER source inventories under `notes/reference/`.
- Added ADRs for precomputed-table queries, code/data separation, attribution labels, and the FEMIC package boundary.
- Added MIT license, code of conduct, and citation metadata.
- Created the private `UBC-FRESH/fresh-tipsy` GitHub repository and pushed the seed on `main`.
- Activated Phase 0 as parent issue #1, set its roadmap status to `active`, and created `feature/p0-bootstrap`. Dashboard at activation: GREEN on lint, format, types, tests, validator, and docs.
- Completed P0.1–P0.3: refreshed the README phase status, removed a duplicated `AGENTS.md` section, and confirmed the attribution and no-authorship statements in `README.md`, `AGENTS.md`, `CITATION.cff`, `LICENSE`, and the docs. Dashboard: GREEN on lint, format, types, tests, validator, and docs.
- Queued the Phase 0 close-out in pull request #2 with `notes/reports/phase-0-closeout.md`; P0 status is `pr-open`. Dashboard: GREEN on lint, format, types, tests, validator, and docs.
- Closed Phase 0: squash-merged pull request #2 as `4bb9776`, deleted `feature/p0-bootstrap`, and closed parent issue #1. Dashboard and CI were green at the merge head.
- Launched Phase 1 as parent issue #3 on `feature/p1-source-inventory`; created child issues #4–#8 for P1.1–P1.5 and started P1.1. Dashboard: GREEN on lint, format, types, tests, validator, and docs.
- Completed P1.1: inventoried 192 TIPSY tables (96 `.tab`, 96 `.taf`, 54,290,043 bytes) and 66 non-database files with SHA-256 manifests; located FAN$IER in a separate `tipsy44/Fansier` tree and recorded it as unvalidated. Added `notes/reference/source-inventory.md` and three manifests. Dashboard: GREEN on lint, format, types, tests, validator, and docs.
- Completed P1.2: documented the `.tab`/`.taf` grammar, filename rules, run-block and PCT/CT treatment semantics, and a 173-row column map with confidence. Added `notes/reference/tab-taf-grammar.md` and `notes/reference/tab-taf-columns.csv`; corrected the duplicate-age explanation in the inventory. Dashboard: GREEN on lint, format, types, tests, validator, and docs.
- Corrected the P1.2 DR duplicate-block description: `dr 2020N00.tab` duplicates its final block, while `dr 2828N00.tab` duplicates block 9.
- Completed P1.3: classified all 269 `OutputColumns.txt` rows and 210 report-column references, mapped `Base` to the 22 `.tab` fields and `Full` to the 151 `.taf` fields, and confirmed zero economics fields in the catalogue. Added `notes/reference/output-columns.md`, `output-columns.csv`, and `report-column-map.csv`. Corrected the seed assumption that product columns are absent from `.taf`; they are present as `model_output`, not measured grades. Resolved the remaining `.tab` positions from the `Base` category. Dashboard: GREEN on lint, format, types, tests, validator, and docs.
- Completed P1.4: froze the data-provenance contract and manifest schema. Added `manifest-schema.md`, a validated `manifest-schema.json`, and `manifest-example.json` for the `pli0530N00` pair; recorded FAN$IER economics, the TIPSY runtime, and the `.taf` mortality aggregation as gaps; made `notes/plan/0002-data-provenance.md` binding. Dashboard: GREEN on lint, format, types, tests, validator, and docs.
- Completed P1.5: redistribution terms for the raw tables are unclear, so real-source fixtures are checksum-only. Added synthetic 22/151-field parser fixtures, `tests/test_fixtures.py`, and `notes/reference/golden-outputs.md`/`.csv` with TIPSY, FAN$IER, and FEMIC candidates and gaps. Dashboard: GREEN on lint, format, types, tests, validator, and docs.
- Queued the Phase 1 close-out in pull request #9 with `notes/reports/phase-1-closeout.md`; P1 status is `pr-open`. Dashboard: GREEN on lint, format, types, tests, validator, and docs.

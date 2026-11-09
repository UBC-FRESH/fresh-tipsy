# Notes

Notes are the persistent, agent-friendly context for this project. They hold
what a future reader, human or agent, needs and cannot get from the code, the
issues, or the changelog alone.

## Plans

- [`plan/0001-program-plan.md`](plan/0001-program-plan.md): mission, scope, phases,
  evidence levels, risks, and first-release definition of done.
- [`plan/0002-data-provenance.md`](plan/0002-data-provenance.md): source classes,
  manifest schema, asset layout, citation, and publication boundary.
- [`plan/0003-architecture.md`](plan/0003-architecture.md): package layout, service
  layer, CLI, API, web UI, assistant, and FEMIC boundary.
- [`plan/0004-validation-release.md`](plan/0004-validation-release.md): validation
  ladder, golden evidence, release checks, and integration gates.

## Reference

- [`reference/tipsy-inventory.md`](reference/tipsy-inventory.md): observed TIPSY
  4.5 install, table formats, species codes, and runtime note.
- [`reference/source-inventory.md`](reference/source-inventory.md): P1.1 install
  inventory, table and file counts, checksum manifests, and FAN$IER status.
- [`reference/tab-taf-grammar.md`](reference/tab-taf-grammar.md): P1.2 `.tab` and
  `.taf` grammar, filename rules, run blocks, and column candidates.
- [`reference/tab-taf-columns.csv`](reference/tab-taf-columns.csv): 173-row
  column map with units, confidence, evidence, and open questions.
- [`reference/output-columns.md`](reference/output-columns.md): P1.3
  classification of `OutputColumns.txt`, report templates, and the economics gap.
- [`reference/output-columns.csv`](reference/output-columns.csv): 269-row
  classification with class, source, evidence, and confidence.
- [`reference/report-column-map.csv`](reference/report-column-map.csv): 210
  report-column references resolved to `OutputColumns.txt` names.
- [`reference/manifest-schema.md`](reference/manifest-schema.md): P1.4 binding
  manifest contract and P2 validation gates.
- [`reference/manifest-schema.json`](reference/manifest-schema.json): JSON Schema
  for the data manifest.
- [`reference/manifest-example.json`](reference/manifest-example.json): validated
  manifest example for a TIPSY `.tab`/`.taf` pair.
- [`reference/golden-outputs.md`](reference/golden-outputs.md): P1.5
  redistribution decision, candidate fixtures, and golden output inventory.
- [`reference/golden-outputs.csv`](reference/golden-outputs.csv): machine-readable
  golden output inventory.
- [`reference/testing.md`](reference/testing.md): test layers, real-source test
  environment variables, and the coverage gate.
- [`reference/curve-validation.md`](reference/curve-validation.md): P3.4 golden
  query set, tolerances, TIPSY comparisons, and the FEMIC TSR gap.
- [`reference/product-schema.md`](reference/product-schema.md): P4.1 typed
  product groups, totals, and mass-balance rules.
- [`reference/tipsy-table-manifest.csv`](reference/tipsy-table-manifest.csv):
  192 TIPSY table entries with IDs, sizes, SHA-256, and header metadata.
- [`reference/tipsy-file-manifest.csv`](reference/tipsy-file-manifest.csv):
  non-database TIPSY files with IDs, sizes, and SHA-256.
- [`reference/fansier-file-manifest.csv`](reference/fansier-file-manifest.csv):
  located FAN$IER files with IDs, sizes, and SHA-256.
- [`reference/fansier-scope.md`](reference/fansier-scope.md): FAN$IER scope,
  inventory gaps, and economics boundary.

## Decisions

- [`adr/0001-query-precomputed-tipsy-tables.md`](adr/0001-query-precomputed-tipsy-tables.md):
  query the tables, do not reimplement TASS.
- [`adr/0002-separate-code-and-data-assets.md`](adr/0002-separate-code-and-data-assets.md):
  code in Git, large assets as release artifacts.
- [`adr/0003-attribution-and-reimplementation-labels.md`](adr/0003-attribution-and-reimplementation-labels.md):
  per-value provenance and evidence labels.
- [`adr/0004-femic-package-boundary.md`](adr/0004-femic-package-boundary.md): FEMIC
  consumes `fresh-tipsy` through an optional dependency.

## Reports

- `reports/`: phase close-out reports. Start from
  [`reports/phase-closeout-template.md`](reports/phase-closeout-template.md).

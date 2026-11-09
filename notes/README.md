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

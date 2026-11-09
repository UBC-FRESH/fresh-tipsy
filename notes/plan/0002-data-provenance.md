# Data and provenance contract

Date: 2026-11-09
Status: binding as of P1.4 (2026-11-09)

## Principles

1. The BC government owns the source models and tables. `fresh-tipsy` does not.
2. Every value must be traceable to a source file and a processing step.
3. Raw government data is not committed to this repository.
4. Small fixtures are allowed; large normalized assets are release artifacts.
5. Reimplemented logic is labelled `reimplemented`, never presented as source
   code from TIPSY or FAN$IER.
6. A missing runtime is recorded as a failed run, not filled with invented data.

## Source roots

Use environment variables or documented discovery:

```text
TIPSY_INSTALL      TIPSY installation root
TIPSY_DATABASE     TIPSY Database directory
FANSIER_INSTALL    FAN$IER installation root, if separate
FRESH_TIPSY_CACHE  local cache for extracted assets
```

Do not hard-code personal or machine-specific paths in tracked files.

## Source classes

### TIPSY database tables

Observed locally:

```text
Database/*.tab
Database/*.taf
```

Likely meaning:

- `.tab` — tab-delimited, compact TASS yield table.
- `.taf` — expanded fixed/tab-delimited TASS output table with more fields.
- headers carry `DatabaseTitle`, `SpeciesName`, `Code`, `SiteFrom`, `SiteTo`,
  `TASSsiteIndex`, `TASSsiteSpecies`, `PNC`, `StockHt`, `StockAge`.
- `[RUN,...]` marks the data block.
- filenames appear to encode species, site range, PNC, and stock-height variant;
  the parser must confirm the grammar from headers rather than assume it.

### TIPSY output schema

Observed locally:

```text
OutputColumns.txt
BatchTIPSY45.tcl
TIPSY45.tcl
*.rpt
```

`OutputColumns.txt` names the runtime output fields, including:

```text
Lumber_Graded_SS_2x4 ... Lumber_Graded_4_2x10
Lumber_Degraded_SS_2x4 ... Lumber_Degraded_4_2x10
Residual_Chips, Residual_Sawdust, Residual_Shavings, Residual_Trim, Residual_Bark
Logs_Grade_D/F/H/I/J/U/X/Y
Industrial_Logs_*
LRF_2_or_Better_All, LRF_Graded_All, LRF_Degraded_All
```

These product fields are TASS/SYLVER model outputs. They are present in the
`.taf` `Full` table and absent from the compact `.tab` table. Label them
`model_output`, never a measured field grade.

### FAN$IER

FAN$IER covers product suites, prices, costs, and financial analysis. Its
internal defaults and economic tables are a separate inventory target. If a
FAN$IER install is not available, the economics layer starts from public
FAN$IER documentation and is labelled `reimplemented`.

## Manifest schema

The contract is binding. The machine-readable schema is
[`../reference/manifest-schema.json`](../reference/manifest-schema.json), the
human-readable contract is
[`../reference/manifest-schema.md`](../reference/manifest-schema.md), and a
validated example is
[`../reference/manifest-example.json`](../reference/manifest-example.json).

The manifest is a JSON envelope:

```json
{
  "manifest_version": "1.2.0",
  "generated_at_utc": "2026-11-09T00:00:00Z",
  "extractor": {"name": "fresh-tipsy", "version": "0.1.0", "parser_version": 1},
  "source_install": {
    "model": "TIPSY",
    "version": "4.5",
    "database_title": "Ministry Standard Database, February 2022",
    "install_env": "TIPSY_INSTALL",
    "database_env": "TIPSY_DATABASE"
  },
  "assets": [],
  "gaps": []
}
```

Each asset records:

- `id`, `kind`, `format`, `role`, `evidence`, and `publication`.
- `source`: model, version, build, database title, relative path, SHA-256, size.
- `table`: pair ID, format, field count, data rows, run count, age range, treatments.
- `columns` or `columns_ref`: positions, names, units, evidence, confidence.
- `citation` and `validation`: status, checks, warnings.
- `notes` for caveats.

Each gap records an unavailable source, runtime, model, or schema, with a reason
and the phase that needs it. A gap is never filled with an invented value.

The `.tab` schema is the 22-row `Base` category; the `.taf` schema is the 151-row
`Full` category. Product and grade columns carry `model_output`. Growth and
stock columns carry `source_table`. Derived columns carry `reimplemented`.

### Manifest validation gates

P2 fails when any of these checks fails:

1. The manifest validates against the schema.
2. Asset and pair IDs are unique; every `.tab`/`.taf` pair is complete.
3. Source paths are relative, with no absolute path or `..`.
4. Every SHA-256 and size matches a fresh recomputation.
5. `.tab` rows have 22 fields; `.taf` rows have 151; zero exceptions.
6. Row counts, run counts, and age ranges match a fresh parse.
7. Pair headers, run counts, and row counts match.
8. Column positions are contiguous and every column has a name, unit, evidence,
   and confidence.
9. Raw sources are `manifest_only`; no raw table is committed.
10. Every citation names the BC source, version, and relative path.
11. No personal path, credential, or secret-shaped string appears.
12. A failed runtime or missing source is a gap, not an invented value.

The full rule list is in
[`../reference/manifest-schema.md`](../reference/manifest-schema.md).

## Asset layout

```text
manifest.json
tables/
  tipsy/
    pli0530n00/
      data.parquet
      metadata.json
  fansier/
    ...
fixtures/
  ...
```

Raw files stay outside the repository. The release includes normalized
Parquet/CSV plus the manifest, not the original install.

## Citation format

Each data page and API response should expose:

```text
Source: Province of British Columbia, TIPSY 4.5, Database/pli0530N00.tab
Extracted: 2026-11-09
Extractor: fresh-tipsy 0.1.0
SHA256: ...
```

For derived outputs:

```text
Source model: TIPSY 4.5 / FAN$IER
Source table: ...
Processing: fresh-tipsy <version>, <command>
Evidence: reimplemented | model_output | validated_against
```

## Publication boundary

- Do not commit `Database/`, `*.tab`, `*.taf`, `*.fns`, `*.brs`, or large
  extracted assets.
- Do commit parsers, schemas, manifests, tests, tiny fixtures, and download
  instructions.
- Do not strip source metadata from a normalized table.
- Do not flatten a table without recording its original columns and units.

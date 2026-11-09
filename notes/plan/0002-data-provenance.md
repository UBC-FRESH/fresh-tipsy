# Data and provenance contract

Date: 2026-11-09
Status: draft, binding once Phase 1 closes

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

These product fields are runtime outputs, not fields in the `.tab`/`.taf`
growth tables.

### FAN$IER

FAN$IER covers product suites, prices, costs, and financial analysis. Its
internal defaults and economic tables are a separate inventory target. If a
FAN$IER install is not available, the economics layer starts from public
FAN$IER documentation and is labelled `reimplemented`.

## Manifest schema

Each extracted asset gets one manifest entry:

```yaml
id: tipsy-pli0530n00
kind: tipsy_database_table
source_model: TIPSY
source_version: "4.5"
source_file: "Database/pli0530N00.tab"
source_sha256: "<sha256>"
extracted_at_utc: "2026-11-09T00:00:00Z"
extractor: "fresh-tipsy 0.1.0"
parser_version: 1
species_code: PLI
species_name: Lodgepole Pine
site_from: 5
site_to: 30
pnc: N
stock_height_m: 0.13
columns:
  - age
  - site_height_m
  - volume_gross_m3_ha
row_count: 13
units:
  age: years
  volume_gross_m3_ha: m3/ha
citation: "Province of British Columbia. TIPSY 4.5 database."
notes: ""
```

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

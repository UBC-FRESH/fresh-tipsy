# Data manifest contract

Date: 2026-11-09
Version: `1.2.0`
Status: binding for P2 and later extraction work
Schema: [`manifest-schema.json`](manifest-schema.json)
Example: [`manifest-example.json`](manifest-example.json)
Program contract: [`../plan/0002-data-provenance.md`](../plan/0002-data-provenance.md)

## Purpose

Every extracted table, fixture, normalized asset, and golden output carries one manifest entry. The entry records where the value came from, which parser produced it, how it is validated, whether it may be published, and which evidence label applies.

The manifest is a release artifact and a test input. It is not a place for raw government data. Raw tables stay outside the repository; their paths and checksums are recorded.

## Envelope

| Field | Required | Meaning |
| --- | --- | --- |
| `manifest_version` | yes | Semantic version of this schema; currently `1.2.0` |
| `generated_at_utc` | yes | ISO 8601 UTC timestamp ending in `Z` |
| `extractor` | yes | `name`, `version`, optional `parser_version`, optional `command` |
| `source_install` | yes | Source model, version, install environment variable, database title, notes |
| `assets` | yes | One or more asset entries |
| `gaps` | no | Known unavailable sources, runtime gaps, model gaps, or schema gaps |

`extractor.version` is the `fresh-tipsy` package version. `extractor.parser_version` is an integer that increments when the parser grammar changes.

## Asset fields

| Field | Required | Meaning |
| --- | --- | --- |
| `id` | yes | Stable slug; lowercase letters, digits, and hyphens |
| `kind` | yes | `tipsy_table`, `fansier_file`, `normalized_table`, `fixture`, `golden_output`, `schema`, `report_template`, `support_file`, `binary`, or `documentation` |
| `format` | yes | `tab`, `taf`, `parquet`, `csv`, `json`, `txt`, `rpt`, `tcl`, `pdf`, `dbf`, `shp`, `exe`, `dll`, `rgm`, `tip`, or `other` |
| `role` | yes | `source_table`, `release_asset`, `fixture`, `golden_output`, `schema`, `report_template`, or `support_file` |
| `evidence` | yes | Evidence label, see below |
| `publication` | yes | `commit`, `release_asset`, or `manifest_only` |
| `source` | yes | Source model, version, relative path, SHA-256, size |
| `table` | for `tipsy_table` and `normalized_table` | Pair ID, source format, field count, row count, run count, age range, treatment list |
| `metadata` | for `tipsy_table` and `normalized_table` | Species code, species name, site range, PNC, and optional stock/treatment metadata |
| `artifact` | for `normalized_table` and every `release_asset` | Released file path, SHA-256, and size |
| `source_asset_ids` | for `normalized_table` | IDs of the source assets the normalized file came from |
| `columns` | one of `columns` or `columns_ref` for `tipsy_table` | Column definitions |
| `columns_ref` | one of `columns` or `columns_ref` for `tipsy_table` | Versioned reference to a committed column map |
| `column_count` | no | Number of columns in `columns_ref` |
| `citation` | yes | BC source citation for the asset |
| `validation` | yes | Status, checks, warnings |
| `notes` | no | Free text; must not contain a personal path or a credential |

## Source fields

| Field | Required | Meaning |
| --- | --- | --- |
| `model` | yes | `TIPSY` or `FANSIER` |
| `version` | yes | Model version, or `unreported` when the source does not state it |
| `build` | no | TASS/SYLVER build string from the table header |
| `database_title` | no | Database edition |
| `relative_path` | yes | Path relative to the install root; no absolute path and no `..` |
| `sha256` | yes | Lowercase 64-character SHA-256 |
| `size_bytes` | yes | Exact byte size |

## Table fields

`table` is required for `tipsy_table`:

| Field | Required | Meaning |
| --- | --- | --- |
| `pair_id` | no | Shared ID for the `.tab`/`.taf` pair |
| `format` | yes | `tab` or `taf` |
| `field_count` | yes | 22 for `.tab`, 151 for `.taf` |
| `data_rows` | yes | Non-empty data rows, excluding padding |
| `run_count` | yes | Number of `[RUN,...]` blocks |
| `first_age`, `last_age` | no | Observed age range |
| `field_count_rule` | no | Human-readable field-count rule |
| `treatments` | no | `PCT`, `CT`, or both |

## Table metadata fields

`metadata` is required for `tipsy_table`:

| Field | Required | Meaning |
| --- | --- | --- |
| `species_code` | yes | Uppercase species code |
| `species_name` | yes | Species display name |
| `site_from` | yes | Minimum site index |
| `site_to` | yes | Maximum site index |
| `pnc` | yes | `C`, `N`, or `P` |
| `stock_height_m` | no | Planting stock height |
| `stock_age_years` | no | Planting stock age |
| `pct_height_m` | no | PCT treatment height |
| `ct_height_m` | no | CT treatment height |

The catalog reads these fields to filter by species, site index, PNC, and stock height without opening the source table.

## Normalized asset fields

A normalized asset adds:

| Field | Required | Meaning |
| --- | --- | --- |
| `artifact` | yes | `relative_path`, `sha256`, and `size_bytes` of the released CSV or Parquet file |
| `source_asset_ids` | yes | The source table asset ID or IDs |
| `table` | yes | Source table format, field count, rows, runs, and treatments |
| `metadata` | yes | The same species/site/PNC/stock metadata as the source |

`publication` is `release_asset`. The raw source remains `manifest_only` and is not committed.

## Column fields

Each column entry has:

- `position`: zero-based field position.
- `name`: `OutputColumns.txt` name or documented candidate.
- `units`: source unit.
- `evidence`: `source_table`, `model_output`, `reimplemented`, `validated_against`, `experimental`, or `unavailable`.
- `confidence`: `high`, `medium`, or `low`.
- `notes`: optional caveat.

Positions must be contiguous from `0` to `field_count - 1`. Every public column has a name, a unit, and a confidence. An unknown column keeps a stable candidate name and `low` confidence; it is not dropped or assigned an invented meaning.

## Evidence labels

| Label | Use |
| --- | --- |
| `source_table` | Directly read from a TIPSY/FAN$IER table, including gridded growth and stock fields |
| `model_output` | TASS/SYLVER/FAN$IER model result; all product, lumber, residue, log-grade, and industrial-log fields |
| `reimplemented` | Computed by `fresh-tipsy` from documented inputs, such as MAI, VPT, carbon, CO2e, and product totals |
| `validated_against` | Matches a named golden output within a stated tolerance |
| `experimental` | Documented but not fully validated |
| `unavailable` | No source or runtime available; recorded as a gap, never filled with invented values |

## Publication boundary

| `publication` | Use | Committed? |
| --- | --- | --- |
| `commit` | Tiny fixtures, schemas, manifests, and tests | yes |
| `release_asset` | Normalized Parquet/CSV and golden assets | no; released with a checksum manifest |
| `manifest_only` | Raw TIPSY/FAN$IER source tables | no; the path and checksum are recorded |

No raw `.tab`, `.taf`, `.fns`, `.brs`, or large normalized table is committed. A manifest entry for a raw source is `manifest_only`.

## Stable IDs

- Asset IDs are lowercase slugs: `^[a-z0-9][a-z0-9-]*$`.
- Table IDs use `tipsy45-db-<stem>-<format>`, for example `tipsy45-db-pli0530n00-tab`.
- Pair IDs use `tipsy45-<stem>`, for example `tipsy45-pli0530n00`.
- Fixtures use `fixture-<purpose>-<stem>`.
- Golden outputs use `golden-<model>-<purpose>-<stem>`.
- IDs never change when the content is re-extracted with the same source; a source change creates a new source version or a new ID.

## Validation rules for P2

P2 must fail the build when any of these checks fails:

1. The manifest and every example validate against `manifest-schema.json`.
2. `manifest_version` is semantic, and `generated_at_utc` is UTC with a `Z`.
3. Every asset ID and pair ID is unique.
4. Every `tipsy_table` pair has exactly one `.tab` and one `.taf`, with matching pair ID.
5. Every source path is relative, contains no `..`, and resolves under the declared install environment.
6. Every source SHA-256 and size matches a fresh recomputation; the manifest records the check.
7. Every `.tab` has 22 fields and every `.taf` has 151 fields per non-empty data row; zero exceptions.
8. Table row counts, run counts, and age ranges match a fresh parse.
9. The header `File` equals the filename stem.
10. The `.tab` and `.taf` headers, run counts, and row counts match.
11. Column positions are contiguous; every column has a name, unit, evidence, and confidence.
12. Product, lumber, residue, log-grade, and industrial-log columns carry `model_output`.
13. Growth and stock columns carry `source_table`; derived columns carry `reimplemented`.
14. Raw source assets use `publication: manifest_only`; no raw table is committed.
15. A failed runtime or missing source becomes a `gaps` entry with `unavailable`, `blocked`, or `planned`; it is not filled with invented values.
16. Every citation names the BC source, the model version, and the relative source path.
17. No personal path, credential, or secret-shaped string appears in the manifest or a referenced fixture.
18. `columns_ref` points to a committed, versioned column map, and `column_count` matches the reference.
19. A normalized asset lists the source asset IDs it came from and carries its own SHA-256 and size.
20. A fixture is small enough to commit and carries the same source metadata as its parent table.

## Gaps

A gap records what is not available:

- `unavailable_source`: FAN$IER price/cost tables are not parsed.
- `runtime_gap`: the TIPSY .NET runtime fails under Wine.
- `schema_gap`: the `.taf` mortality-summary aggregation needs confirmation.
- `model_gap`: a documented model output cannot be reproduced yet.

Each gap names its reason, the phase that needs it, and a note that no value may be invented.

## Versioning

- Schema changes increment `manifest_version` and add a changelog entry.
- Parser grammar changes increment `extractor.parser_version`.
- Source changes increment `source.version` or create a new source asset ID.
- Normalized asset changes create a new release-asset checksum; the source entries remain stable.

## Reconciliation with P1.1 and P1.3

- P1.1 table manifest fields map to `source` and `table`.
- P1.1 file manifest entries map to `support_file`, `report_template`, `schema`, `binary`, or `documentation` assets when they are part of the data contract.
- P1.2 `.tab`/`.taf` columns map to `columns` or `columns_ref`.
- P1.3 product and grade fields carry `model_output`; growth and stock fields carry `source_table`; derived fields carry `reimplemented`.
- The 22 `Base` fields and 151 `Full` fields are the authoritative column counts for the schema checks.

## Attribution

The source data is the work of the Province of British Columbia. The manifest records the source model, version, relative path, checksum, extraction time, and citation. `fresh-tipsy` is the interoperability layer; it does not claim authorship of TIPSY, FAN$IER, TASS, or the source tables.

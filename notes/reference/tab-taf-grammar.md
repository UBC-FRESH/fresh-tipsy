# `.tab` and `.taf` grammar (P1.2)

Date: 2026-11-09
Status: observed and cross-checked against TIPSY 4.5 data; P1.2 evidence
Scope: file grammar, header metadata, filename grammar, run blocks, and column candidates
Related: [`source-inventory.md`](source-inventory.md), [`tab-taf-columns.csv`](tab-taf-columns.csv), [`tipsy-table-manifest.csv`](tipsy-table-manifest.csv), [`../plan/0002-data-provenance.md`](../plan/0002-data-provenance.md)

## Evidence base

- 192 TIPSY 4.5 database files: 96 `.tab` and 96 `.taf`.
- Header fields from every file, checked against the filename.
- 8,278 `[RUN,...]` blocks and 246,048 data rows.
- Cross-checks between `.tab` fields and the `.taf` stock, volume, product, biomass, and mortality columns.
- The local TIPSY 4.4 help file (`TIPSY44.chm`) for the definitions of yield-table variables, crown cover, and treatment settings.
- `OutputColumns.txt` for the 151-field `.taf` order, names, and units.

No raw table is committed. The machine-readable column map is in [`tab-taf-columns.csv`](tab-taf-columns.csv).

## Byte-level grammar

- ASCII text.
- CRLF line endings in the raw files.
- Tab-delimited fields.
- No header row inside the data block. The only field labels are in the external schema files.
- Blank or all-empty rows occur as padding at the start of a run block and must be skipped.

## File grammar

```text
[TASS SPECIES]
<key>=<value>
<key>=<value>
...
[RUN,<initial_density>,<pct_density>,<ct_density>]
<padding rows>
<data rows>
[RUN,...]
<padding rows>
<data rows>
...
```

- The first line is always `[TASS SPECIES]`.
- The header block is a sequence of `key=value` lines.
- The first `[RUN,...]` line ends the header.
- Every `[RUN,...]` line starts a new run block.
- A file contains multiple run blocks; do not assume one block per file or one age series per file.
- Whitespace-only lines and all-empty tab rows are padding, not data.
- A data row has exactly 22 fields in `.tab` and exactly 151 fields in `.taf`.

## Header grammar

Required keys observed in all 192 files:

| Key | Meaning | Example |
| --- | --- | --- |
| `DatabaseTitle` | Database edition | `Ministry Standard Database, February 2022` |
| `File` | Table stem; matches the filename without its extension | `pli0530N00` |
| `SpeciesName` | Species display name | `Lodgepole Pine` |
| `Source` | TASS build and run-date range | `v3.01.13W (Feb 2017 - Jul 2021)` |
| `Code` | Species code | `PLI` |
| `SiteFrom` | Minimum site index in the table | `5` |
| `SiteTo` | Maximum site index in the table | `30` |
| `TASSsiteIndex` | TASS site-index reference | `23` |
| `TASSsiteSpecies` | TASS surrogate species | `PLI` |
| `PNC` | Planted/natural/clumped code | `N`, `P`, or `C` |

Optional keys:

| Key | Files | Meaning |
| --- | ---: | --- |
| `PCT` | 48 `.tab`/`.taf` pairs | Pre-commercial thinning height (m); `4` or `6` observed |
| `CT` | 30 pairs | Commercial thinning height (m); `16`, `18`, `21`, `22`, `27`, or `33` observed |
| `StockHt` | 36 pairs | Planting stock height (m); `0.13` or `0.21` observed |
| `StockAge` | 36 pairs | Stock age at planting; `0` observed |

- `File` matches the filename stem in all 192 files.
- `Code` and `SpeciesName` agree in all files.
- The header is the authority for species, site range, PNC, and treatment metadata. The filename repeats part of it but not `StockHt` or `StockAge`.

## Filename grammar

Observed pattern, matched by all 96 table pairs:

```text
^(?P<species>[a-z]{2,3})\s?(?P<site_from>\d{2})(?P<site_to>\d{2})(?P<pnc>[CNP])(?P<pct>\d{2})(?P<ct>\d{2})?$
```

Examples:

| Filename stem | Species | Site from | Site to | PNC | PCT code | CT code |
| --- | --- | ---: | ---: | --- | --- | --- |
| `pli0530N00` | PLI | 5 | 30 | N | `00` | none |
| `at 1032C00` | AT | 10 | 32 | C | `00` | none |
| `at 1032C04` | AT | 10 | 32 | C | `04` | none |
| `fdc1050N0021` | FDC | 10 | 50 | N | `00` | `21` |
| `cw 1040N06` | CW | 10 | 40 | N | `06` | none |

Rules:

- Species codes are lowercase in the filename and uppercase in the header.
- Some filenames contain a space between the species and the site digits.
- Site bounds are two digits each. This is lossless for the observed ranges (5 to 50).
- The PNC letter is uppercase.
- The two-digit PCT code is `00` when PCT is absent, otherwise it equals the `PCT` header value (`04` or `06`).
- The optional two-digit CT code equals the `CT` header value.
- `StockHt` and `StockAge` are not encoded in the filename.
- The header remains the authority. Parse the filename only as a convenience and verify it against the header.

### PCT and CT semantics

- `PCT=<value>` is the pre-commercial thinning height in metres. In `at 1032C04`, the stems drop at the height-4.0 row, and the duplicate age-7 rows mark the pre-thin and post-thin states.
- `CT=<value>` is the commercial thinning height in metres. In `fdc1050N0021`, the stems drop at height 21.0, and the duplicate age-32 rows mark the pre-thin and post-thin states.
- The treatment height is recorded in the header, not inferred from the treatment row.

## Run-block grammar

`[RUN,<initial_density>,<pct_density>,<ct_density>]`

| Parameter | Meaning | Observed values |
| --- | --- | --- |
| initial density | Stems per hectare at establishment | 69 to 250,000 |
| PCT density | Stems per hectare after PCT; `0` when absent | 0, 69, 100, 156, 331, 494, 816, 1600, 4444 |
| CT density | Stems per hectare after CT; `0` when absent | 0, 69, 100, 156, 331, 494, 625, 816 |

- `[RUN,x,0,0]` is an untreated run.
- `[RUN,x,y,0]` is a PCT run with residual density `y`.
- `[RUN,x,0,z]` is a CT run with residual density `z`.
- The first data row in a block is sometimes an all-empty padding row; the next rows are the age series.
- A treatment appears as two rows with the same age: the first is the pre-treatment state, the second the post-treatment state. Preserve both rows and expose a treatment-boundary flag. Do not deduplicate by age.

### Duplicate-age evidence

- 5,174 adjacent duplicate-age pairs occur in the `.tab` files, and the same count occurs in the matching `.taf` files.
- Duplicates occur in 65 `.tab` files.
- 63 of those files carry a PCT or CT header; the duplicates line up with the treatment boundaries.
- The remaining two files have a malformed duplicate-age block rather than a treatment: the final block of `dr 2020N00.tab` (11 duplicate pairs) and block 9 of `dr 2828N00.tab` (8 duplicate pairs). Record them as data defects, not treatments.

## Data-row grammar

- First field: TIPSY age in years. It is blank on some padding rows and on the first row of some blocks.
- Remaining fields: numeric values, blank when not applicable.
- Decimal points use `.`; thousands separators are not used.
- Empty fields are meaningful (zero, not applicable, or not computed). The parser must keep the empty-versus-zero distinction until P2 defines the column semantics.

## `.tab` column map

The `.tab` table is the compact yield table. Its 22 fields match the 22 rows of the `OutputColumns.txt` `Base` category in order. P1.3 resolved the earlier unknowns: positions 16-18 are crop-tree fields, positions 19-21 are TASS height fields, and positions 2-3 are `VolumeGross` and `Volume000`.

| Position | Name | Unit | Confidence | Evidence |
| ---: | --- | --- | --- | --- |
| 0 | `YearTASS_Base` | years | high | `Base` row 0; matches `.taf` `YearTASS_Full` on every sampled row |
| 1 | `HeightSindex_Base` | m | high | `Base` row 1; matches `.taf` `HeightSindex_Full` |
| 2 | `VolumeGross` | m³/ha | high | `Base` row 2; gross whole-stand volume |
| 3 | `Volume000` | m³/ha | high | `Base` row 3; total standing 0.0+ volume |
| 4 | `Volume125` | m³/ha | high | `Base` row 4; equals the sum of `.taf` `Volume_Diameter_Class_*` |
| 5 | `Volume175` | m³/ha | high | `Base` row 5; equals the sum of the 20 cm-and-larger stock-volume rows |
| 6 | `BasalArea000` | m²/ha | high | `Base` row 6; recomputed from the `.taf` stock table |
| 7 | `BasalArea125` | m²/ha | high | `Base` row 7; stock classes 15+ |
| 8 | `BasalArea175` | m²/ha | high | `Base` row 8; stock classes 20+ |
| 9 | `MeanDBHg000` | cm | high | `Base` row 9; quadratic mean DBH from the stock table |
| 10 | `MeanDBHg125` | cm | high | `Base` row 10; stock classes 15+ |
| 11 | `MeanDBHg175` | cm | high | `Base` row 11; stock classes 20+ |
| 12 | `StemCount000` | #/ha | high | `Base` row 12; equals the sum of `.taf` `Stems_Diameter_Class_*` |
| 13 | `StemCount125` | #/ha | high | `Base` row 13; stock classes 15+ |
| 14 | `StemCount175` | #/ha | high | `Base` row 14; stock classes 20+ |
| 15 | `CrownCover` | % | high | `Base` row 15; crown-cover curve |
| 16 | `Crop250VolUtil125` | m³/ha | high | `Base` row 16; crop-tree volume 12.5+ |
| 17 | `Crop250DBHgMean` | cm | high | `Base` row 17; crop-tree mean DBH |
| 18 | `Crop250LiveCrown` | % | high | `Base` row 18; crop-tree live crown |
| 19 | `HeightTassTop` | m | high | `Base` row 19; TASS top height |
| 20 | `HeightTassMean` | m | high | `Base` row 20; TASS mean height |
| 21 | `HeightTassPredom` | m | high | `Base` row 21; TASS predominant height |

The machine-readable map is in [`tab-taf-columns.csv`](tab-taf-columns.csv).

## `.taf` column map

The 151 `.taf` fields match the 151 rows of the `Full` category in `OutputColumns.txt` in order. The complete row-by-row map, with units and confidence, is in [`tab-taf-columns.csv`](tab-taf-columns.csv).

Group summary:

| Positions | Content | Confidence |
| --- | --- | --- |
| 0-1 | `YearTASS_Full`, `HeightSindex_Full` | high |
| 2-10 | Lumber (#2 & Better) and mill residues | high |
| 11-15 | Mortality summary: stems, mean DBH, mean height, basal area, volume | medium |
| 16-29 | Mortality stock: stems and volume by size class | high |
| 30-48 | Stems by diameter class (0 to 90 cm) | high |
| 49-67 | Volume by diameter class (0 to 90 cm) | high |
| 68-75 | Log volume by grade (D, F, H, I, J, U, X, Y) | high |
| 76-78 | Juvenile volume (0.0+, 12.5+, 17.5+) | high |
| 79-88 | Live and dead biomass by component | high |
| 89-90 | Mean height to crown base and mean crown length | high |
| 91-110 | Graded lumber by grade and dimension | high |
| 111-130 | Degraded (juvenile-wood adjusted) lumber | high |
| 131-150 | Industrial logs (conifer and deciduous) | high |

Column-order checks:

- The sum of positions 30-48 equals `.tab` position 12 (total trees) on every sampled row.
- The sum of positions 49-67 equals `.tab` position 4 (merch volume) on every sampled row.
- Positions 68-75 populate only when logs exist; positions 91-150 populate only when lumber or industrial logs exist.
- Positions 79-88 behave as biomass components in `ODT/ha`.

Mortality-summary caveat:

- Positions 12 and 13 are named `Mortality_DBHg_Mean` and `Mortality_Height_Mean` in `OutputColumns.txt`, but their raw values do not behave like simple means. They are retained with medium confidence and flagged in the CSV. Do not publish them as means until a TASS schema or a runtime output confirms the aggregation.

## Validation evidence

- 192 files: 96 `.tab` with 22 fields per data row, 96 `.taf` with 151 fields per data row; 0 field-count exceptions.
- 8,278 run markers; 246,048 non-empty data rows; 1,384 rows with a blank first field.
- All 96 `.tab`/`.taf` pairs match on header content, run count, and row count.
- 12 pairs have different age sequences between `.tab` and `.taf` even though headers, run counts, and row counts match. Each reader must use its own table's age grid; do not assume row alignment across formats.
- All 192 files have `File` equal to the filename stem.
- Filename pattern matched all 96 stems.
- `.tab` positions 12-14 equal cumulative stock-table stem sums on sampled rows.
- `.tab` positions 4-5 equal cumulative stock-table volume sums on sampled rows.
- `.tab` positions 6-11 equal stock-table basal-area and DBHq recomputations on sampled rows.
- `[RUN]` density parameters match the observed post-treatment stem counts.
- The two DR malformed blocks are recorded as data defects: the final block of `dr 2020N00.tab` and block 9 of `dr 2828N00.tab`.

## Open questions for P2 and P3

- Confirm the `Mortality_DBHg_Mean` and `Mortality_Height_Mean` aggregation.
- Decide whether P2 stores one row per age with a treatment-boundary flag, or one row per raw record. The raw order must be preserved either way.
- Confirm the PCT/CT threshold rule: the observed treatment row is the first row at or above the header height, with a pre-treatment row retained at the same age.

## Attribution

The files described here are the work of the Province of British Columbia. Cite TIPSY 4.5 and the relative source path:

```text
Province of British Columbia
TIPSY 4.5
Database/<file>
```

`fresh-tipsy` is the interoperability layer; it does not claim authorship of TIPSY, TASS, or the source tables.

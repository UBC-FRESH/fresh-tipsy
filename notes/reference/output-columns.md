# Output column classification (P1.3)

Date: 2026-11-09
Status: complete; classification evidence for P2 and P4
Scope: `OutputColumns.txt`, 17 report templates, table-backed versus runtime columns, and the economics gap
Related: [`source-inventory.md`](source-inventory.md), [`tab-taf-grammar.md`](tab-taf-grammar.md), [`output-columns.csv`](output-columns.csv), [`report-column-map.csv`](report-column-map.csv), [`tab-taf-columns.csv`](tab-taf-columns.csv)

## Method

- Parsed all 269 rows of `OutputColumns.txt` (12 columns per row).
- Mapped the `Base` category to the 22 `.tab` fields and the `Full` category to the 151 `.taf` fields, using the P1.2 position map.
- Parsed the 17 `.rpt` report templates: 210 report-column references and 166 unique column names. All 210 references resolve to an `OutputColumns.txt` name or a documented Tcl alias.
- Inspected the `*COLUMNS` and `*HEADERS` sections of `TIPSY45.tcl` for runtime and economics fields.
- Did not invent a product coefficient, grade assignment, or price.
- The machine-readable row-level map is in [`output-columns.csv`](output-columns.csv). The report map is in [`report-column-map.csv`](report-column-map.csv).

## Correction to the seed assumption

The seed said that TIPSY product columns are runtime outputs and are not columns in the `.tab` or `.taf` growth tables. That is only half right:

- The compact `.tab` table does **not** contain product or grade columns.
- The `.taf` `Full` table **does** contain them. They are TASS/SYLVER model outputs and are read directly from the `.taf` fields.
- They remain `model_output`, not measured field grades. They are precomputed for the TIPSY database scenarios; fresh-tipsy can expose them but cannot generate new ones without a TASS/SYLVER run.

`notes/reference/tipsy-inventory.md`, `notes/reference/source-inventory.md`, `notes/plan/0001-program-plan.md`, and `notes/plan/0002-data-provenance.md` were corrected to match this finding.

## Category classification

| `OutputColumns.txt` category | Rows | Class | Source | Evidence | Confidence |
| --- | ---: | --- | --- | --- | --- |
| `Base` | 22 | `table_base` | `Database/*.tab` positions 0-21 | `source_table` | high |
| `Full` (growth/stock) | 74 | `table_full` | `Database/*.taf` positions 0-150 | `source_table` | high, except mortality summary |
| `Full` (product/grade) | 77 | `table_full_product` | `Database/*.taf` positions 0-150 | `model_output` | high, except mortality summary |
| `BaseCalc` | 6 | `derived_base` | MAI and VPT formulas on `Base` | `reimplemented` | high |
| `Calc` | 11 | `derived_runtime` | TIPSY runtime | `reimplemented` or `model_output` | medium |
| `choose` | 10 | `selectable_runtime` | Runtime utilization selection | `model_output` | medium |
| `FullCalc` (product aggregates) | 7 | `derived_full_product` | Sums of `Full` product fields | `model_output` | high |
| `FullCalc` (other) | 62 | `derived_full` | Carbon, CO2e, VPT, biomass totals, juvenile percent, crown bulk density | `reimplemented` | high |
| **Total** | **269** | | | | |

Evidence totals:

- `source_table`: 96 rows (22 `Base` + 74 growth/stock `Full`).
- `model_output`: 99 rows (77 product `Full` + 5 OAF/genetic/fertilization `Calc` + 10 `choose` + 7 product `FullCalc`).
- `reimplemented`: 74 rows (6 `BaseCalc` + 6 age/height `Calc` + 62 non-product `FullCalc`).

## Product and grade fields

The 77 product/grade fields in the `Full` category:

| Group | Count | Examples |
| --- | ---: | --- |
| Lumber #2 & Better by dimension | 4 | `Lumber_2_or_Better_2x4` ... `2x10` |
| Mill residues | 5 | `Residual_Chips`, `Residual_Sawdust`, `Residual_Shavings`, `Residual_Trim`, `Residual_Bark` |
| Log grades | 8 | `Logs_Grade_D`, `F`, `H`, `I`, `J`, `U`, `X`, `Y` |
| Graded lumber by grade and dimension | 20 | `Lumber_Graded_SS_2x4` ... `Lumber_Graded_4_2x10` |
| Degraded (juvenile-wood adjusted) lumber | 20 | `Lumber_Degraded_SS_2x4` ... `Lumber_Degraded_4_2x10` |
| Industrial logs, conifer and deciduous | 20 | `Industrial_Logs_D38L13` ... `Industrial_Logs_D152` |

The 7 product aggregates in `FullCalc`:

- `Logs_Grade_All`
- `Lumber_2_or_Better_All`
- `Lumber_Graded_All`
- `Lumber_Degraded_All`
- `LRF_2_or_Better_All`
- `LRF_Graded_All`
- `LRF_Degraded_All`

Rules:

- Every product and grade field carries `model_output`. It is not a measured BC field grade.
- The `.taf` values are scenario-specific precomputed outputs. A new scenario needs a TASS/SYLVER run.
- Phase 4 must add the mass-balance checks: lumber grade and dimension sum to the lumber total; residues reconcile with the source total where available.
- The LRF fields are derived ratios, not independent measurements.

## Growth and stock fields

- The 22 `Base` fields are the `.tab` schema: age, site height, gross/total/merchantable volumes, basal area, mean DBH, stem counts, crown cover, crop-tree volume/DBH/live crown, and TASS top/mean/predominant height.
- The 74 growth/stock `Full` fields are the `.taf` growth and stock columns: age, site height, mortality summary and size classes, stems and volume by diameter class, juvenile volume, biomass components, and crown metrics.
- Both groups carry `source_table` because they are read directly from a TIPSY table. The table itself is a TASS model output; the label records the direct source, not a field measurement.
- `.taf` positions 11-15 remain `medium` confidence. `Mortality_DBHg_Mean` and `Mortality_Height_Mean` do not behave like simple means and must not be published as means until confirmed.

## Derived and runtime fields

### `BaseCalc` (6)

`MAI000`, `MAI125`, `MAI175`, `VPT000`, `VPT125`, `VPT175`.

- `MAI` is volume divided by TIPSY age.
- `VPT` is volume divided by stem count.
- Class `derived_base`, evidence `reimplemented`.

### `Calc` (11)

- `Year`, `TotalAge`, `BHAge`, `StandAge`, `HeightSindex`, `Height` are age and height derivations. Evidence `reimplemented`.
- `GWgain`, `FertGain`, `OAFremoval`, `OAFmortality`, `OAFimpact` are TIPSY model adjustments. Evidence `model_output`.

### `choose` (10)

`OAF`, `Volume`, `BasalArea`, `DBHg`, `SPH`, `MAI`, `VPT`, `CC`, `Juvenille_Volume`, `Juvenille_Percent`.

- These are runtime columns at a user-selected utilization level.
- They are not stored columns; the selector and interpolation are TIPSY runtime behaviour.
- Class `selectable_runtime`, evidence `model_output`.

### `FullCalc` (69)

- Product aggregates (7) are `model_output`.
- `VPT_Diameter_Class_*` (19) are derived volume per tree by diameter class.
- `Mortality_VPT_Size_Class_*` (7) are derived mortality volume per tree.
- `Biomass_Live_Total`, `Biomass_Live_Above`, `Biomass_Dead_Total`, `Biomass_Dead_Above` are sums of the `Full` biomass components.
- `Carbon_*` and `CO2e_*` apply the documented `BIOtoCarbon` and `BIOtoCO2e` conversions to the biomass components.
- `Juvenille_Percent000/125/175` are derived percentages.
- `Crown_Bulk_Density` is derived from crown geometry.
- These are `reimplemented` formulas over `Full` fields, not stored columns.

## Report templates

The 17 `.rpt` templates contain 210 column references. All resolve.

| Report | Columns | Notes |
| --- | ---: | --- |
| `Biomass.rpt` | 16 | `Year`, `Height`, live/dead biomass components and totals |
| `CO2e.rpt` | 16 | `Year`, `Height`, live/dead CO2e components and totals |
| `Carbon.rpt` | 16 | `Year`, `Height`, live/dead carbon components and totals |
| `ForestLandscapePlan.rpt` | 2 | `VolumeGross`, `CC` |
| `Industrial.rpt` | 22 | `Year`, `Height`, 20 industrial-log fields |
| `Logs.rpt` | 11 | `Year`, `Height`, 8 log grades, `Logs_Grade_All` |
| `Lumber.rpt` | 9 | `Year`, `Height`, #2 & Better dimensions, total, chips, LRF |
| `Mortality.rpt` | 13 | `Year`, `Height`, mortality summary and 7 size classes |
| `Stand.rpt` | 21 | `Year`, `Height`, 19 stems-by-diameter classes |
| `Stock.rpt` | 21 | `Year`, `Height`, 19 volume-by-diameter classes |
| `TimberSupply SQL.rpt` | 5 | `Year`, conifer/deciduous volume and height aliases |
| `TimberSupply.rpt` | 6 | Conifer/deciduous volume and height, `VolumeGross`, `CC` |
| `VPT.rpt` | 21 | `Year`, `Height`, 19 volume-per-tree classes |
| `VolHtMai.rpt` | 3 | `Volume:125`, `Height`, `MAI:125` |
| `Volume.rpt` | 5 | `Year`, `Height`, gross, 0.0+, 12.5+ |
| `Wildlife.rpt` | 9 | `Year`, `Height`, volume, basal area, DBH, SPH, VPT, crown cover |
| `Yield.rpt` | 14 | Standard yield fields plus crop-tree fields |

Report aliases:

| Report name | Resolved `OutputColumns.txt` name | Notes |
| --- | --- | --- |
| `Year` | `Year` (`Calc`) | TIPSY age |
| `Height` | `Height` (`Calc`) | Site-height derivation |
| `CC` | `CrownCover` (`Base`) | Crown cover |
| `Volume:000` | `Volume000` (`Base`) | Tcl colon notation |
| `Volume:125` | `Volume125` (`Base`) | Tcl colon notation |
| `Volume:Auto` | `Volume` (`choose`) | Runtime utilization |
| `Volume:Auto:Con` | `Volume` (`choose`) | Runtime utilization and conifer component |
| `Volume:Auto:Dec` | `Volume` (`choose`) | Runtime utilization and deciduous component |
| `Height:Con` | `Height` (`Calc`) | Conifer component |
| `Height:Dec` | `Height` (`Calc`) | Deciduous component |
| `BasalArea:000` | `BasalArea000` (`Base`) | Tcl colon notation |
| `DBHg:000` | `MeanDBHg000` (`Base`) | Tcl colon notation |
| `SPH:000` | `StemCount000` (`Base`) | Tcl colon notation |
| `VPT:000` | `VPT000` (`BaseCalc`) | Tcl colon notation |
| `MAI:125` | `MAI125` (`BaseCalc`) | Tcl colon notation |
| `MAI:Auto` | `MAI` (`choose`) | Runtime utilization |

Report class counts: `table_full` 59, `derived_full` 54, `table_full_product` 33, `derived_runtime` 32, `table_base` 17, `selectable_runtime` 13, and `derived_base` 2.

## Economics

`OutputColumns.txt` contains **zero** price, cost, NPV, discount, revenue, or sensitivity fields. Economics is not in the growth catalogue.

`TIPSY45.tcl` `*HEADERS` exposes these TIPSY/FAN$IER runtime fields:

```text
Harvest Revenue
Tree-to-Truck Cost
Haul Costs
Milling Cost
Average Revenue
Conversion Cost
NPV
Site Value
SV Discount +1%
SV Discount -1%
SV Revenue +10%
SV Revenue -10%
SV Conv. Cost +10%
SV Conv. Cost -10%
SV Regen. Cost +10%
SV Regen. Cost -10%
SV Post-Regen. Cost +10%
SV Post-Regen. Cost -10%
```

Classification:

- Class `runtime_economics`; evidence `unavailable` until a validated TIPSY/FAN$IER run or a documented FAN$IER price/cost table is captured.
- The FAN$IER inventory has `Fansier.exe`, help files, and `Samples/sample.fns`; no price or cost table has been parsed.
- Do not invent a price, cost, discount rate, or sensitivity coefficient.
- Phase 4 starts from public FAN$IER documentation and labels the result `reimplemented` or `model_output` as appropriate.

## Validation evidence

- 269 `OutputColumns.txt` rows classified; every row has a class, source, evidence label, and confidence.
- 22 `Base` rows match the 22 `.tab` fields; 151 `Full` rows match the 151 `.taf` fields.
- 77 `Full` product fields plus 7 `FullCalc` product aggregates carry `model_output`.
- 210 report-column references across 17 templates resolved; 0 unresolved.
- Zero economics fields in `OutputColumns.txt`.
- No product coefficient, grade assignment, or price was invented.
- Dashboard GREEN on lint, format, types, tests, validator, and docs.

## Open questions

- Confirm the `.taf` mortality-summary aggregation at positions 11-15.
- Capture the FAN$IER price/cost tables or a validated economic run before P4 publishes an economic value.
- Confirm the report alias semantics that depend on runtime utilization (`Volume:Auto`, `MAI:Auto`) with a working runtime or a fixture.

## Attribution

The source columns are the work of the Province of British Columbia. Cite TIPSY 4.5 and the relative source path. `fresh-tipsy` is the interoperability layer; it does not claim authorship of TIPSY, FAN$IER, TASS, or the source tables.

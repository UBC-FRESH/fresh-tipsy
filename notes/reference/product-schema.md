# Product schema (P4.1)

Date: 2026-11-09
Status: complete
Scope: typed TIPSY product columns, units, evidence, and mass-balance rules
Related: [`output-columns.md`](output-columns.md), [`tab-taf-columns.csv`](tab-taf-columns.csv), [`../../src/fresh_tipsy/products/schema.py`](../../src/fresh_tipsy/products/schema.py)

## Product fields

The `.taf` `Full` table contains 77 product and grade fields. All are `model_output`, never measured field grades.

| Group | Count | `.taf` positions | Units |
| --- | ---: | --- | --- |
| `Lumber_2_or_Better` | 4 | 2-5 | `bf/ha` |
| `Residual_*` | 5 | 6-10 | `ODT/ha` |
| `Logs_Grade_*` | 8 | 68-75 | `m³/ha` |
| `Lumber_Graded_*` | 20 | 91-110 | `bf/ha` |
| `Lumber_Degraded_*` | 20 | 111-130 | `bf/ha` |
| `Industrial_Logs_*` | 20 | 131-150 | `m³/ha` |

Lumber grades are `SS`, `1`, `2`, `3`, and `4`; dimensions are `2x4`, `2x6`, `2x8`, and `2x10`. The `SS` grade is stored as `SS` in the field name; the other grades use `1`, `2`, `3`, and `4`.

## Product totals

These aggregates are not stored in `.taf`; they are TIPSY/SYLVER totals or derived ratios.

```text
Lumber_2_or_Better_All
Lumber_Graded_All
Lumber_Degraded_All
Logs_Grade_All
LRF_2_or_Better_All
LRF_Graded_All
LRF_Degraded_All
```

## Mass-balance rules

| Rule | Total | Components | Tolerance |
| --- | --- | ---: | --- |
| `lumber_2_or_better` | `Lumber_2_or_Better_All` | 4 | `1e-6` |
| `lumber_graded` | `Lumber_Graded_All` | 20 | `1e-6` |
| `lumber_degraded` | `Lumber_Degraded_All` | 20 | `1e-6` |
| `logs` | `Logs_Grade_All` | 8 | `1e-6` |
| `residues` | none stored | 5 | `1e-6` |

The residue components are reported individually because the extracted tables have no residue total. P4.3 must record that check as unavailable rather than inventing a remainder.

## Source contract

- Every field maps to a packaged `.taf` column position and unit.
- The schema test compares all 77 names, positions, and units with `tab-taf-columns.csv`.
- No coefficient, grade assignment, or measured BC log grade is added.

## Attribution

The product columns are TASS/SYLVER model outputs read from the BC TIPSY 4.5 `.taf` tables. `fresh-tipsy` is the interoperability layer; it does not claim authorship of the source model or data.

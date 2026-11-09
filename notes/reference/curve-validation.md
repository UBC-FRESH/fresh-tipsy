# Growth query validation (P3.4)

Date: 2026-11-09
Status: TIPSY table comparisons complete; FEMIC TSR comparison unavailable
Scope: representative exact-age and interpolated growth queries
Related: [`golden-outputs.md`](golden-outputs.md), [`testing.md`](testing.md), [`tab-taf-grammar.md`](tab-taf-grammar.md), [`../plan/0004-validation-release.md`](../plan/0004-validation-release.md)

## Golden query set

| Query | Source | Check | Tolerance |
| --- | --- | --- | --- |
| `SYN`, site 5, age 2 | synthetic `.tab` | `height_site` equals the synthetic row value | `1e-9` |
| `PLI`, site 20, PNC N, stock height 0.13, age 36 | `pli0530N00.tab` | gross volume, top height, stems, and DBH equal the raw row | `1e-9` |
| `PLI`, site 20, PNC N, stock height 0.13, age 38.5 | `pli0530N00.tab` | gross volume equals the midpoint of the age-36 and age-41 rows | `1e-6` |

The real-source queries read the installed table through `TIPSY_DATABASE`. They do not commit source values. The source table is identified by relative path and SHA-256 in the query result provenance.

## TIPSY comparison

The exact-age test verifies that the selected table, row lookup, metric mapping, and provenance wiring return the source value unchanged. The interpolation test verifies that the midpoint of two source rows is reproduced within `1e-6`.

These are source-table regression checks. They do not independently validate TASS physics; the source table is the reference.

## FEMIC TSR comparison

No redistributable FEMIC TSR output has been captured. `notes/reference/golden-outputs.md` records the `golden-femic-tsr` entry as `not_captured`.

The comparison remains a gap:

- Do not invent a FEMIC value or tolerance.
- When a TSR output is available, record its relative path, SHA-256, query inputs, extraction command, and tolerance here.
- A future test may read an environment variable such as `FEMIC_TSR`; until then, the path is skip-only and does not count as a pass.

## TIPSY runtime

The local TIPSY .NET Framework 4.8 runtime fails under Wine. This does not block the table-based comparisons above. Custom runtime output remains unavailable and is recorded as a runtime gap.

## Evidence labels

- Direct source-table values: `source_table`.
- Derived `.taf` sums and stock metrics: `reimplemented`.
- A future FEMIC comparison that matches within tolerance: `validated_against`.
- Missing FEMIC evidence: `unavailable`; it is not reported as a pass.

## Reproduction

```bash
TIPSY_DATABASE="$TIPSY_INSTALL/Database" python -m pytest tests/test_curve_golden.py -q
```

Without `TIPSY_DATABASE`, the real-source tests skip. The synthetic comparison runs everywhere.

## Known limits

- The comparison covers one real species/site/table pair. It is a representative check, not full database coverage.
- Interpolation is linear by design; the source tables are the only reference.
- FEMIC TSR evidence is absent.
- Carbon metrics remain unavailable until a documented conversion factor is sourced.

# Product recovery and mass balance (P4.3)

Date: 2026-11-09
Status: complete
Scope: product aggregation, totals, mass-balance checks, and failure behavior
Related: [`product-schema.md`](product-schema.md), [`product-goldens.md`](product-goldens.md), [`../../src/fresh_tipsy/products/recovery.py`](../../src/fresh_tipsy/products/recovery.py)

## API

`CurveEngine.products(query)` selects a `.taf` table and returns a
`ProductRecovery`. The standalone `recover_products(result)` accepts an existing
`QueryResult`.

```python
from fresh_tipsy.curves import CurveEngine, CurveQuery

engine = CurveEngine.from_manifest(manifest_path, source_root=database_root)
recovery = engine.products(
    CurveQuery(
        "PLI",
        20,
        age=36,
        pnc="N",
        stock_height_m=0.13,
        format="taf",
    )
)
```

A `.tab` query raises `ProductUnavailableError` because the compact table has no
product columns.

## Groups and units

| Group | Count | Units | Evidence |
| --- | ---: | --- | --- |
| `#2 & Better` dimensions | 4 | `bf/ha` | `model_output` |
| Mill residues | 5 | `ODT/ha` | `model_output` |
| Log grades | 8 | `m³/ha` | `model_output` |
| Graded lumber | 20 | `bf/ha` | `model_output` |
| Degraded lumber | 20 | `bf/ha` | `model_output` |
| Industrial logs | 20 | `m³/ha` | `model_output` |

`ProductRecovery` exposes each group as typed `ProductQuantity` values plus a
`ProductTotals` object. Every value keeps the source field, units, group, grade,
dimension or code, and the `model_output` label. Provenance carries the source
asset, path, SHA-256, version, and citation.

## Mass-balance checks

| Check | Comparison | Independent |
| --- | --- | --- |
| `lumber_2_or_better` | four #2 & Better dimensions to the aggregate | no |
| `lumber_graded` | twenty graded dimensions to the aggregate | no |
| `lumber_degraded` | twenty degraded dimensions to the aggregate | no |
| `logs` | eight log grades to the aggregate | no |
| `residues` | five components; no stored total | no |
| `lumber_2_or_better_vs_graded` | #2 & Better to graded SS/#1/#2 | yes |

The `.taf` `Full` table does not store `Lumber_2_or_Better_All`,
`Lumber_Graded_All`, `Lumber_Degraded_All`, or `Logs_Grade_All`. Those totals
are FullCalc/TIPSY aggregates, and the custom runtime that would print them is
unavailable. The four aggregate checks therefore compare a derived total with
its own components and are marked `independent=False`; they catch missing or
unreadable components, not an independent source total. This limitation is
recorded rather than hidden.

The #2 & Better cross-check uses independent stored fields. It passes when the
aggregate equals graded SS, #1, and #2. Some tables (`dr` is the observed case)
place every graded grade in the #2 & Better aggregate; for those tables the
check reconciles against all five grades and records that in its note. A true
mismatch fails.

Residues have no total in the source. The residue check returns
`status="unavailable"` and a component sum; it does not invent a remainder.

## Failure behavior

`recover_products` is strict by default. Any check with `status="fail"` raises a
typed `MassBalanceError` naming the failed check. Passing `strict=False` returns
the recovery with the failed checks for inspection or reporting. Blank product
columns produce `status="unavailable"`, not failures, so young or non-product
rows remain queryable.

## Verification

- Synthetic tests cover passing totals, a failing #2 & Better cross-check, the
  all-grade fallback, a compact-table rejection, and blank product columns.
- Real-source PLI queries at ages 36, 55, and 91 pass every available check.
- A read-only scan of all 96 `.taf` tables found 65,230 rows with reconciling
  #2 & Better values, 1,586 rows with a #2 & Better value but no graded
  breakdown (`unavailable`), and zero failures.
- No raw product value is committed. The scan was a verification step, not a
  data release.

## Limits

- No stored product aggregate is compared independently.
- No product-plus-residue-plus-loss total can be reconciled because the source
  does not provide the common-unit total.
- No measured BC log grade is read, inferred, or claimed.
- Product values are model output, not field grades.

# Release validation (P6.1)

Date: 2026-11-09
Status: TIPSY growth/product regression complete; FEMIC TSR unavailable
Scope: release golden checks against representative TIPSY tables
Related: [`curve-validation.md`](curve-validation.md), [`product-recovery.md`](product-recovery.md), [`economics.md`](economics.md), [`../plan/0004-validation-release.md`](../plan/0004-validation-release.md)

## Golden set

| Species | Table | Site | PNC | Age | Check |
| --- | --- | ---: | --- | ---: | --- |
| PLI | `pli0530N00.tab` / `.taf` | 20 | N | 36 | gross volume and product mass balance |
| FDC | `fdc1050N00.tab` / `.taf` | 30 | N | 36 | gross volume and product mass balance |
| AT | `at 1032C00.tab` / `.taf` | 20 | C | 45 | gross volume and log-grade recovery |
| FDI | `fdi0535C00.tab` / `.taf` | 20 | C | 49 | gross volume and product mass balance |

Tolerances:

- exact-age growth value: `1e-9`;
- product mass balance: `1e-6`;
- hand-checked NPV: `1e-6`;
- sensitivity direction: monotonic sign.

## Commands

```bash
TIPSY_DATABASE="$TIPSY_INSTALL/Database" python -m pytest \
  tests/test_release_golden.py \
  tests/test_curve_golden.py \
  tests/test_product_regression.py \
  tests/test_economics.py -q
```

The real-source checks skip when `TIPSY_DATABASE` is unset. They read source
tables through the install path and do not copy values or files into the
repository.

## Results

- PLI, FDC, AT, and FDI exact-age gross volumes match the source `.tab` row.
- Product recovery runs without a failing mass-balance check; AT exposes log
  grades but no lumber aggregate, which is recorded as `unavailable` per check.
- Residues remain `unavailable` where the source provides no residue total.
- The hand-checked economics case still yields NPV 335.543289 CAD/ha and SV
  546.081251 CAD/ha.
- Sensitivity directions remain monotonic for price, cost, and discount changes.

## FEMIC gap

No redistributable FEMIC TSR output is captured. `golden-outputs.csv` records
`golden-femic-tsr` as `not_captured`; the release check reports it as
`unavailable`, not as a pass.

When an output becomes available, record:

- relative path and SHA-256;
- query inputs and source version;
- extraction command and date;
- tolerance and evidence label `validated_against`.

## Known limits

- Four representative tables cover the release smoke check, not all 96 pairs.
- The source tables are the reference; this does not independently validate
  TASS physics.
- FAN$IER remains unparsed and unvalidated.
- TIPSY custom runtime and FEMIC TSR remain unavailable.
- Carbon remains unavailable.

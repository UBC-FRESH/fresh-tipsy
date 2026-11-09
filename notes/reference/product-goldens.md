# Product golden inventory (P4.2)

Date: 2026-11-09
Status: TIPSY `.taf` candidates are checksum-only; custom runtime and FAN$IER product evidence are gaps
Scope: product and grade outputs for P4.3 and later
Related: [`product-schema.md`](product-schema.md), [`golden-outputs.md`](golden-outputs.md), [`../plan/0004-validation-release.md`](../plan/0004-validation-release.md)

## Redistribution decision

The product columns are BC TIPSY/TASS/SYLVER model output. Redistribution terms for raw or extracted product values are unclear, so this phase stores **checksums, paths, and query inputs only**. No raw `.taf` row or product value is committed.

## Product golden query set

| Candidate | Species | Site | PNC | Stock height | Ages | Product groups |
| --- | --- | ---: | --- | ---: | --- | --- |
| `pli0530N00.taf` | PLI | 20 | N | 0.13 | 36, 55, 91 | lumber, residues, log grades, graded/degraded lumber, industrial logs |
| `fdc1050N00.taf` | FDC | 30 | N | unspecified | 36, 47, 53 | lumber, residues, log grades, graded/degraded lumber, industrial logs |
| `at 1032C00.taf` | AT | 20 | C | unspecified | 45, 52, 100 | lumber, residues, log grades, graded/degraded lumber, industrial logs |
| `fdi0535C00.taf` | FDI | 20 | C | 0.21 | 49, 54, 100 | lumber, residues, log grades, graded/degraded lumber, industrial logs |

The full inventory, checksums, and reproduction commands are in [`product-goldens.csv`](product-goldens.csv).

## Source checksums

| File | Size | SHA-256 |
| --- | ---: | --- |
| `pli0530N00.taf` | 124,361 | `569d57639c86b7360b7a577599c37688b38c2060a8f8202ed82548de7238581d` |
| `fdc1050N00.taf` | 183,242 | `87204c42dac598b46e2463dac58ba72a8d0ed75cc02f0d6068fc509285d11a84` |
| `at 1032C00.taf` | 127,470 | `30e93b777dca0e4d85907be71ff51d11d48889393a99c9c4bdeb03703620a0de` |
| `fdi0535C00.taf` | 217,025 | `fe922b9d1e20f9b3e94ca0cd11c5b21fb1b33f93b69b1d27e4ede132145f91c8` |

## Runtime attempt

The TIPSY `.NET Framework 4.8` runtime fails under Wine before producing custom output. The recorded prior attempt used the TIPSY batch/report path and crashed without a product report. P4.2 did not repeat the crash: the runtime failure is a recorded gap, and no custom product value was invented.

When a working runtime or archived output exists, record:

- source model and version;
- source table or report;
- relative path and SHA-256;
- report/query inputs;
- extraction command and date;
- evidence label `model_output`.

## FAN$IER evidence

- `Fansier.exe`, `Fansier.chm`, `activities.ez`, `help.ez`, and `Samples/sample.fns` are located.
- No price table, cost table, product suite, or validated FAN$IER economic run has been parsed.
- `golden-fansier-sample` is `located_not_validated`; `golden-fansier-product-suite` is `unavailable`.
- P4.4 must start from public documentation and label its logic `reimplemented`; it must not invent a price or cost.

## Reproduction

Set the source roots through environment variables. Do not hard-code a host path.

```bash
sha256sum "$TIPSY_DATABASE/pli0530N00.taf"
sha256sum "$FANSIER_INSTALL/Samples/sample.fns"
```

The checksums must match [`product-goldens.csv`](product-goldens.csv).

## Gaps

- No custom TIPSY product report is captured.
- No parsed FAN$IER price/cost/product-suite table.
- No measured BC log-grade evidence is available or claimed.
- Product values remain `model_output`; they are not field grades.

## Attribution

The source product columns are the work of the Province of British Columbia. Cite TIPSY 4.5 and the relative source path. `fresh-tipsy` is the interoperability layer; it does not claim authorship of the source tables or model.

# Release assets (P6.3)

Date: 2026-11-09
Status: 0.1.0 assets published; raw and normalized data withheld
Scope: publishable package artifacts, stable manifests, and withheld raw data
Related: [`package-build.md`](package-build.md), [`manifest-schema.md`](manifest-schema.md), [`../adr/0002-separate-code-and-data-assets.md`](../adr/0002-separate-code-and-data-assets.md)

## Publication decision

- Package artifacts: published in the `v0.1.0` GitHub release.
- Data manifest and checksum inventories: published in the repository; they do
  not contain raw table bodies.
- Raw TIPSY tables: withheld. Redistribution terms are unclear.
- Normalized TIPSY assets: withheld with the raw tables. Users rebuild them from
  a local licensed install.
- FAN$IER artifacts: inventory-only. No price or cost table is parsed or
  redistributed.

The machine-readable asset register is
[`release-assets.csv`](release-assets.csv). Every repository asset records its
source, version, path, SHA-256, and citation. Every release-pending artifact
records its build checksum.

## Asset set

| Asset | Publication | Notes |
| --- | --- | --- |
| Wheel `fresh_tipsy-0.1.0-py3-none-any.whl` | published | Built and smoke-tested |
| Sdist `fresh_tipsy-0.1.0.tar.gz` | published | Built and smoke-tested |
| Docs `fresh-tipsy-0.1.0-docs.zip` | published | Sphinx HTML; Pages deploy unavailable on the private plan |
| Example data manifest | repository | Schema 1.2.0; validates against the packaged schema |
| Table/file/FAN$IER manifests | repository | Checksums only; no raw table bodies |
| Raw TIPSY tables | withheld | Rebuild from a local install |
| Normalized TIPSY assets | withheld | Rebuild with `db extract` and the `parquet` extra |

The stable data-manifest schema remains `1.2.0`. A full extraction manifest is
generated at release time from the local source tree; the committed example
proves schema and provenance behavior without redistributing data.

## Checksums

Package checksums from the P6.2 build:

```text
24cb9f343cd463eec7f70d139dd592405575561586247add4a854affec554055  fresh_tipsy-0.1.0-py3-none-any.whl
ecffe98b017b154a94ac55dcca6f3f22a6a3db9685817ae7af605115e2097af5  fresh_tipsy-0.1.0.tar.gz
```

Repository manifest checksums are in `release-assets.csv`.

## Validation

```bash
python scripts/check_release_assets.py /path/to/release --manifest /path/to/manifest.json --json
```

The validator:

- requires `checksums.txt` and checks every listed file;
- rejects raw `.tab`, `.taf`, `.fns`, `.brs`, `.rgm`, and `.tip` files;
- optionally validates the data manifest against the packaged schema;
- returns a structured JSON summary and non-zero exit on failure.

Tests are in `tests/test_release_assets.py`.

## Rebuild withheld data

```bash
pip install "fresh-tipsy[parquet]"
fresh-tipsy db extract --source "$TIPSY_INSTALL" --out "$FRESH_TIPSY_CACHE"
fresh-tipsy db validate --catalog "$FRESH_TIPSY_CACHE/manifest.json" --source "$TIPSY_INSTALL"
```

The extracted manifest carries source paths, versions, SHA-256, and citations.
A user must obtain the source tables under their own licence terms.

## Release action

Published as tag `v0.1.0` on 2026-11-09. The tag and release contain the wheel,
sdist, docs archive, checksums, and release notes. GitHub Pages is unavailable on
the current private-repository plan, so the docs workflow builds successfully
and the HTML is attached to the release. Raw and normalized TIPSY assets remain
withheld.

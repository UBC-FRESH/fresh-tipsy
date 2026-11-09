# Release assets (P6.3)

Date: 2026-11-09
Status: asset set and checksums prepared; publication pending separate approval
Scope: publishable package artifacts, stable manifests, and withheld raw data
Related: [`package-build.md`](package-build.md), [`manifest-schema.md`](manifest-schema.md), [`../adr/0002-separate-code-and-data-assets.md`](../adr/0002-separate-code-and-data-assets.md)

## Publication decision

- Package artifacts: prepared for a future release; no tag or GitHub release is
  created without separate approval.
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
| Wheel `fresh_tipsy-0.1.0-py3-none-any.whl` | release pending approval | Built and smoke-tested in P6.2 |
| Sdist `fresh_tipsy-0.1.0.tar.gz` | release pending approval | Built and smoke-tested in P6.2 |
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
5570bdb7cf9a8a18f35b46b96b085a80b6cef5114ae1aefa0650eb5f452a7a05  fresh_tipsy-0.1.0-py3-none-any.whl
82af94eea106ea2aab95428925831e787689290296ec1d9c2345811b5ca5bdf0  fresh_tipsy-0.1.0.tar.gz
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

## Release action still required

Creating a tag, GitHub release, or uploading the prepared wheel/sdist is a
separate approval. This task records the asset set and checksums but does not
publish them.

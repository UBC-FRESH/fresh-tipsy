# Citation instructions

Date: 2026-11-09
Status: 0.1.0 release preparation
Scope: code, data manifest, and source-data attribution

## Cite fresh-tipsy

Use `CITATION.cff` or this text:

> UBC FRESH Lab. 2026. fresh-tipsy, version 0.1.0. A provenance-first
> interoperability layer for BC TIPSY and FAN$IER data tables.
> https://github.com/UBC-FRESH/fresh-tipsy

Cite the exact package version and, when available, the data-manifest SHA-256
and source table path. Do not cite `fresh-tipsy` as the author of TIPSY,
FAN$IER, TASS, or FEMIC.

## Cite the source models and tables

TIPSY:

> Province of British Columbia. TIPSY 4.5. Ministry Standard Database,
> February 2022. Source build v3.01.13W (Feb 2017 - Jul 2021).
> `Database/<table>.tab` and `.taf`, SHA-256 `<digest>`.

FAN$IER, when referenced:

> Province of British Columbia. FAN$IER forest economics model. Source version
> unreported in the local inventory; no price or cost table is redistributed.

FEMIC, when a future comparison is used:

> Province of British Columbia. FEMIC. Cite the exact output, version, path,
> SHA-256, query inputs, and extraction date.

The local source inventory and checksums are in:

- [`tipsy-table-manifest.csv`](tipsy-table-manifest.csv)
- [`tipsy-file-manifest.csv`](tipsy-file-manifest.csv)
- [`fansier-file-manifest.csv`](fansier-file-manifest.csv)
- [`source-inventory.md`](source-inventory.md)

## Cite the data manifest

For a generated extraction manifest, cite:

```text
fresh-tipsy data manifest, schema 1.2.0
manifest SHA-256: <digest>
TIPSY source version: 4.5
database: Ministry Standard Database, February 2022
```

The committed [`manifest-example.json`](manifest-example.json) is an example for
the `pli0530N00` pair, not a redistribution of the table. A full extraction
manifest is generated locally from a licensed install.

## What is redistributed

- Code and documentation: MIT.
- Manifest example and checksum inventories: repository metadata, no table
  bodies.
- Raw TIPSY tables and normalized assets: withheld; rebuild from a local
  licensed install.
- Synthetic test fixtures: original test data, clearly marked synthetic, not BC
  source data.

No licence is granted here for BC data or model outputs. Users must obtain the
source under the applicable BC terms.

## Rebuild withheld data

```bash
pip install "fresh-tipsy[parquet]"
fresh-tipsy db extract --source "$TIPSY_INSTALL" --out "$FRESH_TIPSY_CACHE"
fresh-tipsy db validate --catalog "$FRESH_TIPSY_CACHE/manifest.json" \
  --source "$TIPSY_INSTALL"
```

Record the generated manifest SHA-256 with any published result.

## Evidence labels in citations

- `source_table`: direct table value.
- `model_output`: TASS/SYLVER product or grade output.
- `reimplemented`: documented formula or derived value.
- `validated_against`: matched a named reference within tolerance.
- `unavailable`: no source, runtime, or golden output.

Economics results remain `reimplemented` and unvalidated against FAN$IER.
Product grades are not measured field grades.

## Release action

This document prepares citation text for 0.1.0. No tag, GitHub release, or
upload is created without separate approval.

# TIPSY and FAN$IER source inventory (P1.1)

Date: 2026-11-09
Status: observed from the local installs; P1.1 evidence
Scope: TIPSY 4.5 database, schema, reports, and samples; FAN$IER availability
Related: [`tipsy-inventory.md`](tipsy-inventory.md), [`tab-taf-grammar.md`](tab-taf-grammar.md), [`tab-taf-columns.csv`](tab-taf-columns.csv), [`tipsy-table-manifest.csv`](tipsy-table-manifest.csv), [`tipsy-file-manifest.csv`](tipsy-file-manifest.csv), [`fansier-file-manifest.csv`](fansier-file-manifest.csv), [`../plan/0002-data-provenance.md`](../plan/0002-data-provenance.md)

## Method

- Discovery uses `TIPSY_INSTALL`, `TIPSY_DATABASE`, and `FANSIER_INSTALL`. No absolute path is recorded here.
- Every file entry records a stable ID, relative path, size in bytes, and SHA-256.
- Table rows were read with a read-only standard-library pass: header key/value lines up to the first `[RUN,...]`, then every `[RUN,...]` block, ignoring rows whose fields are all empty.
- Tables were not parsed into a committed normalized form, and no raw table is committed.
- The inventory files are manifests, not data assets.

## TIPSY 4.5 installation

- 192 database tables: 96 `.tab` and 96 `.taf`, 54,290,043 bytes total.
- 66 non-database files: 11,231,159 bytes total.
- Two database titles: `Ministry Standard Database, February 2022` (160 tables) and `Ministry Standard Database, March 2023` (32 tables).
- Table IDs follow `tipsy45-db-<slug>-<format>`, for example `tipsy45-db-pli0530n00-tab`.
- File IDs follow `tipsy45-file-<slug>`, for example `tipsy45-file-outputcolumns-txt`.

The complete table list is in [`tipsy-table-manifest.csv`](tipsy-table-manifest.csv). The complete non-database list is in [`tipsy-file-manifest.csv`](tipsy-file-manifest.csv).

## Database tables

### Species

| Code | Species name | Pairs | Files |
| --- | --- | ---: | ---: |
| PLI | Lodgepole Pine | 24 | 48 |
| DR | Red Alder | 16 | 32 |
| FDC | Coastal Douglas-fir | 16 | 32 |
| AT | Trembling Aspen | 6 | 12 |
| FDI | Interior Douglas-fir | 6 | 12 |
| HWC | Coastal Western Hemlock | 6 | 12 |
| SW | White Spruce | 6 | 12 |
| CW | Western Redcedar | 4 | 8 |
| HWI | Interior Western Hemlock | 4 | 8 |
| NC | Non-Commercial | 4 | 8 |
| SS | Sitka Spruce | 4 | 8 |

### PNC and title

| Field | Values | Files |
| --- | --- | ---: |
| PNC | `N` | 80 |
| PNC | `P` | 80 |
| PNC | `C` | 32 |
| Title | February 2022 | 160 |
| Title | March 2023 | 32 |

### Source builds

| Header `Source` value | Files |
| --- | ---: |
| `v3.01.13W (Feb 2017 - Jul 2021)` | 48 |
| `v2.05.24f (Apr 2014 - Apr 2014)` | 44 |
| `v2.07.28WS (Apr 2014 - Mar 2018)` | 32 |
| `v2.07.55WS (Apr 2014 - Oct 2017)` | 20 |
| `v2.07.73WS (Apr 2012 - Jul 2021)` | 12 |
| `v3.01.15W (Jul 2017 - Jul 2021)` | 12 |
| `v2.05.24f (Apr 2014 - Jul 2021)` | 8 |
| `v2.06.54DS (Apr 2014 - Jul 2021)` | 8 |
| `v2.06.54DS (Apr 2014 - Apr 2014)` | 8 |

The table `Source` value identifies the build that produced the table; the installation is TIPSY 4.5.

### Header fields

Every `.tab` and `.taf` file starts with `[TASS SPECIES]` and a key/value header. Observed keys:

```text
DatabaseTitle
File
SpeciesName
Source
Code
SiteFrom
SiteTo
TASSsiteIndex
TASSsiteSpecies
PNC
[PCT]          optional, 96 files
[CT]           optional, 60 files
[StockHt]      optional, 72 files
[StockAge]     optional, 72 files
```

- The `File` header matches the filename stem in all 192 files.
- `TASSsiteIndex` is `0` in 120 files, `23` in 48, `25` in 12, and `20` in 12.
- `StockHt` is `0.13` in 48 files and `0.21` in 24 files; when present, `StockAge` is `0`.
- `PCT` is `4` in 50 files and `6` in 46 files.
- `CT` values observed: `16`, `18`, `21`, `22`, `27`, and `33`.
- `SiteFrom` values observed: 5, 10, 20, 24, 28, and 32. `SiteTo` values range from 20 to 50.

### Format observations for P1.2

These are observations for the grammar task, not a parser contract.

- Files are ASCII with CRLF line endings and tab-delimited rows.
- The header ends at the first `[RUN,...]` line. A file contains multiple run blocks, each introduced by another `[RUN,...]` line.
- There are 8,278 run markers in total: 4,139 in `.tab` files and 4,139 in `.taf` files.
- Every non-empty data row has exactly 22 fields in `.tab` and 151 fields in `.taf`; there are no field-count exceptions in the 192 files.
- There are 246,048 data rows in total: 123,024 in `.tab` files and 123,024 in `.taf` files.
- 1,384 rows have an empty first field. These are padding or leading rows and must not be treated as age-zero data without a rule.
- 5,174 adjacent duplicate age pairs occur in the `.tab` files, and the same count occurs in the matching `.taf` files, across 65 files. 63 of those files carry a PCT or CT header and the duplicates mark treatment boundaries; the other two are malformed duplicate-age blocks: the final block of `dr 2020N00.tab` and block 9 of `dr 2828N00.tab`. Strict age monotonicity cannot be assumed, and the treatment rows must be preserved. See [`tab-taf-grammar.md`](tab-taf-grammar.md).
- Each `.tab` file has a matching `.taf` file. For all 96 pairs, the headers, run counts, and row counts match.
- Table size range: 15,458 to 1,678,256 bytes. Run count range: 12 to 179. Data-row range: 204 to 4,953.
- Observed ages range from 1 to 501.
- Filenames use lowercase species codes and sometimes contain spaces, such as `at 1032C00.tab`. Use the header `File`, `Code`, and other key/value fields as the authoritative identity; treat the filename as a convenience.

Open questions for P1.2:

- The meaning of the three numeric parameters in `[RUN,...]`.
- The rule for duplicate ages within a run block.
- The meaning and use of `PCT`, `CT`, `TASSsiteIndex`, and `TASSsiteSpecies`.
- The filename grammar after the header fields are taken as the source of truth.

These are resolved or narrowed in [`tab-taf-grammar.md`](tab-taf-grammar.md); the remaining column-level unknowns are listed there and in [`tab-taf-columns.csv`](tab-taf-columns.csv).

## Output schema, reports, and samples

- `OutputColumns.txt`: 27,794 bytes, SHA-256 `649ecec3ba40d00a83452115c7d489ddaf5ce8ab858924520c3d77c4de845fce`.
  - UTF-8 with a byte-order mark; tab-delimited; 269 rows and 12 columns.
  - Category counts: `Full` 151, `FullCalc` 69, `Base` 22, `Calc` 11, `choose` 10, `BaseCalc` 6.
  - The `Full` category contains 77 product-related rows: lumber, residues, logs, industrial logs, and LRF.
- The product fields are TASS/SYLVER model outputs. They are present in the `.taf` `Full` table and absent from the compact `.tab` table. Treat them as `model_output`, not measured field grades.
- Report templates: 17 `.rpt` files, including Lumber, Logs, Industrial, Volume, Yield, Stock, Stand, Mortality, Biomass, Carbon, CO2e, VPT, and Wildlife reports.
- Tcl definitions: `BatchTIPSY45.tcl`, `TIPSY.tcl`, `TIPSY44.tcl`, `TIPSY45.tcl`, and `Tass_Sum.tcl`.
- Samples: 21 files, including `.Tip` project files, `TIPSY45 Sample.rgm`, exported CSV outputs (`MSYT.csv`, `ex1.csv`, `mck_no_rust.csv`, `tass_input_lakes.csv`), and `VRIsample.dbf`/`VRIsample.shp`.
- Support data: 13 text files, including `TableRange.txt`, `btpfields.txt`, `stockheights.txt`, `vriSpecies.txt`, `defaultStands.txt`, and `utiliz.txt`.
- Binaries: 8 files, including `TIPSYbtc_real.exe` and the WebView2 and site-index libraries.
- Documentation: `userguide1.4.pdf`.

Every file's size and SHA-256 is in [`tipsy-file-manifest.csv`](tipsy-file-manifest.csv).

## FAN$IER

- `FANSIER_INSTALL` is unset, and no `fansier` executable is on `PATH`.
- No FAN$IER file exists inside the TIPSY 4.5 installation.
- A separate `tipsy44/Fansier` tree was located in the workspace. Set `FANSIER_INSTALL` to that directory to reproduce the manifest.
- Files inventoried: `Fansier.exe` (719,792 bytes), `Fansier.chm`, `activities.ez`, `help.ez`, and `Samples/sample.fns`.
- `Fansier.exe` is a PE32 .NET assembly. Its version is not reported by a simple strings scan.
- Status: the executable is located, but it has not been run or validated. Economic outputs remain `unavailable` until a run is captured or public documentation is encoded as `reimplemented`.

See [`fansier-file-manifest.csv`](fansier-file-manifest.csv).

## Runtime status

The TIPSY `.NET Framework 4.8` runtime currently fails under Wine before producing output. Table extraction, including the `.taf` product columns, does not depend on the runtime; custom runtime outputs do. A failed run is recorded as a failed run and is not replaced with invented values.

## Verification

- Table manifest: 192 rows, 192 unique IDs, 0 size or SHA-256 mismatches against the installed files.
- File manifest: 66 rows, 66 unique IDs, 0 size or SHA-256 mismatches.
- FAN$IER manifest: 5 rows, 5 unique IDs, 0 size or SHA-256 mismatches.
- All 96 `.tab`/`.taf` pairs match on headers, run counts, and row counts.
- Field-count check: no exceptions; `.tab` rows are 22 fields and `.taf` rows are 151 fields.

To re-check a manifest after setting the environment variables:

```bash
python - <<'PY'
import csv, hashlib, os

def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()

for manifest, root in [
    ("notes/reference/tipsy-table-manifest.csv", os.environ["TIPSY_INSTALL"]),
    ("notes/reference/tipsy-file-manifest.csv", os.environ["TIPSY_INSTALL"]),
    ("notes/reference/fansier-file-manifest.csv", os.environ["FANSIER_INSTALL"]),
]:
    for row in csv.DictReader(open(manifest, encoding="utf-8")):
        path = os.path.join(root, row["relative_path"])
        assert os.path.getsize(path) == int(row["size_bytes"]), row["relative_path"]
        assert sha256(path) == row["sha256"], row["relative_path"]
PY
```

## Attribution

Every table and file above is the work of the Province of British Columbia. Cite `TIPSY 4.5` and the relative source path, for example:

```text
Province of British Columbia
TIPSY 4.5
Database/pli0530N00.tab
```

FAN$IER files retain the same BC attribution. `fresh-tipsy` is the interoperability layer; it does not claim authorship of these sources.

# TIPSY source inventory

Date: 2026-11-09
Status: observed from the local TIPSY 4.5 installation
Scope: table extraction and output-schema planning

P1.1 inventory: the complete source inventory, counts, and checksum manifests
are in [`source-inventory.md`](source-inventory.md).

## Installation shape

The local TIPSY 4.5 install contains:

```text
Database/             96 .tab files and 96 .taf files, about 53 MB
OutputColumns.txt     runtime output field catalogue
BatchTIPSY45.tcl      batch composer
TIPSY45.tcl           report/UI definitions
*.rpt                 custom report templates
TIPSYbtc.exe          launch wrapper
TIPSYbtc_real.exe     .NET Framework 4.8 application
Samples/              .rgm, .tip, .csv, and sample outputs
```

Use `TIPSY_INSTALL` and `TIPSY_DATABASE` for discovery. Do not commit the
installation.

## Observed database content

The `.tab` headers expose:

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
StockHt
StockAge
[RUN,...]
```

Species codes observed in the local table set:

```text
AT   Trembling Aspen
CW   Western Redcedar
DR   Red Alder
FDC  Coastal Douglas-fir
FDI  Interior Douglas-fir
HWC  Coastal Western Hemlock
HWI  Interior Western Hemlock
NC   Non-Commercial
PLI  Lodgepole Pine
SS   Sitka Spruce
SW   White Spruce
```

PNC variants observed: `C`, `N`, `P`.

The filename grammar is not yet authoritative. Treat the header fields as the
source of truth and use the filename only as a fallback after Phase 1 confirms
the pattern. Filenames use lowercase species codes and sometimes contain spaces,
such as `at 1032C00.tab`.

## Table format observations

- `.tab`: tab-delimited; every non-empty data row has 22 fields.
- `.taf`: tab-delimited; every non-empty data row has 151 fields.
- The files are ASCII with CRLF line endings, not binary.
- Data blocks start after each `[RUN,...]` marker, and a file contains multiple
  run blocks. There are 8,278 run markers across the 192 files.
- Duplicate age values occur within some blocks, so P1.2 must define the age
  key rather than assume strict monotonicity.
- `.tab` is the compact TASS yield table.
- `.taf` is the expanded output table; it still does **not** contain the TIPSY
  product columns.

## Product output schema

`OutputColumns.txt` exposes product fields in the `Full` section:

```text
Lumber_Graded_SS_2x4 ... Lumber_Graded_4_2x10
Lumber_Degraded_SS_2x4 ... Lumber_Degraded_4_2x10
Residual_Chips
Residual_Sawdust
Residual_Shavings
Residual_Trim
Residual_Bark
Logs_Grade_D/F/H/I/J/U/X/Y
Industrial_Logs_D38L13 ... Industrial_Logs_D152
LRF_2_or_Better_All
LRF_Graded_All
LRF_Degraded_All
```

These are TASS/SYLVER model outputs. They are present in the `.taf` `Full` table and absent from the compact `.tab` table. Treat them as `model_output`, not measured field grades. Phase 4 must validate them against a working TIPSY run or an existing output archive; the extraction path does not invent them.

## Runtime note

`TIPSYbtc_real.exe` targets .NET Framework 4.8. A local Wine launch currently
crashes before producing output. This is a runtime engineering issue, not a
table-format issue:

- table extraction, including the `.taf` product columns, does not depend on
  the runtime;
- custom runtime outputs do;
- existing TIPSY/FEMIC output CSVs and fixture archives are valid golden
  sources when the runtime is unavailable;
- a failed runtime is recorded as a failed run, not replaced by invented data.

## Source attribution

Every extracted table and output must cite:

```text
Province of British Columbia
TIPSY 4.5
Database/<file> or <output report>
```

The package is `fresh-tipsy`; the source model is BC TIPSY. Do not blur those.

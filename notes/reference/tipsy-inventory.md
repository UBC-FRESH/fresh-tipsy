# TIPSY source inventory

Date: 2026-11-09
Status: observed from the local TIPSY 4.5 installation
Scope: table extraction and output-schema planning

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
the pattern.

## Table format observations

- `.tab`: tab-delimited; the sample `pli0530N00.tab` row had 22 fields.
- `.taf`: tab-delimited; the sample `pli0530N00.taf` row had 151 fields.
- The files are ASCII, not binary.
- The data block starts after `[RUN,...]`.
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

These are runtime outputs. They are not columns in the `.tab` or `.taf` growth
tables. Phase 4 must obtain them from a working TIPSY run, an existing output
archive, or a documented reimplementation.

## Runtime note

`TIPSYbtc_real.exe` targets .NET Framework 4.8. A local Wine launch currently
crashes before producing output. This is a runtime engineering issue, not a
table-format issue:

- table extraction does not depend on the runtime;
- product-output extraction does;
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

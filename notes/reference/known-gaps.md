# Known gaps at 0.1.0

Date: 2026-11-09
Status: released 0.1.0
Scope: gaps that must remain visible in release notes, API responses, and citations

## Source and runtime

- **TIPSY custom runtime**: the `.NET Framework 4.8` runtime fails under Wine.
  Custom product and FullCalc reports are unavailable.
- **FEMIC TSR**: no redistributable TSR output is captured. The comparison is
  `unavailable`, not a pass.
- **FAN$IER tables**: the executable and sample project are located, but default
  price, cost, product-suite, and NPV tables are not parsed.
- **Raw data redistribution**: TIPSY source tables and normalized assets are
  withheld because redistribution terms are unclear. Rebuild from a local
  licensed install.

## Product recovery

- **Aggregate source totals**: `.taf` stores product components but not
  `Lumber_2_or_Better_All`, `Lumber_Graded_All`, `Lumber_Degraded_All`, or
  `Logs_Grade_All`. Aggregate checks are derived; the independent
  #2 & Better-to-graded cross-check is the hard stored-field check.
- **Residue total**: the source has no residue total. Residue reconciliation is
  recorded as `unavailable`.
- **`dr` convention**: some `dr` tables place all graded grades in the
  #2 & Better aggregate. The cross-check reconciles that convention and records
  it in the check note.
- **Measured grades**: all grade output is TASS/SYLVER `model_output`; it is not
  a measured BC field grade and no mill-specific recovery is provided.

## Economics

- **Validation**: formulas are documented and hand-checked, but unvalidated
  against FAN$IER output.
- **Defaults**: no default price or cost table is embedded. Prices, costs, and
  the discount rate are explicit inputs.
- **Historical proxies**: public FAN$IER documentation describes historical
  2006-dollar averages; this package does not embed them as current prices.
- **Unit conversions**: compatible board-foot/volume/ODT units are supported;
  ODT-to-BDU and other physical conversions are not invented.
- **Scope**: no mill-specific economics, taxes, IRR, or full FAN$IER parity.

## Interfaces

- **FEMIC repository change**: the fresh-tipsy adapter is complete, but the
  FEMIC dependency, adapter call, and backlink are not applied. The FEMIC
  worktree has unrelated changes and external repository changes need separate
  approval.
- **Web economics form**: one price line and one cost line; use CLI/API JSON for
  multi-line scenarios.
- **Assistant**: deterministic tools and prompt guidance only; no live model
  adapter, conversation persistence, or prompt-evaluation suite.
- **Release assets**: wheel, sdist, and HTML docs are published in the `v0.1.0`
  release; raw and normalized TIPSY assets remain withheld.
- **Docs hosting**: GitHub Pages is unavailable on the current private-repository
  plan. The docs workflow builds successfully and skips deployment; HTML is
  attached to the release.

## Data and metrics

- **Carbon**: no stored carbon columns or documented conversion factor; carbon
  metrics remain unavailable.
- **Mortality**: `.taf` mortality positions 11-15 remain medium confidence and
  are not exposed as simple public means.
- **Golden coverage**: four representative species are checked, not all 96
  table pairs.
- **No raw data**: committed fixtures are synthetic only; real-source tests read
  through `TIPSY_DATABASE` and skip when unset.

## Release checks

- Minimal `db extract` requires the `parquet` extra.
- The web/API extras are optional.
- No source table, personal path, or invented coefficient is packaged.
- The data manifest schema remains `1.2.0`.

## Attribution

The source models and tables are the work of the Province of British Columbia.
`fresh-tipsy` is the interoperability layer; it does not relicense the source
data or claim authorship of TIPSY, FAN$IER, TASS, or FEMIC.

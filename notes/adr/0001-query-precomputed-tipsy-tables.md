# ADR 0001: Query precomputed TIPSY tables instead of reimplementing TASS

Status: proposed
Date: 2026-11-09
Issues: TBD

## Context

TIPSY ships a database of precomputed TASS yield tables. The tables are plain
ASCII and contain the growth surfaces for species, site index, PNC, and stock
height variants.

Reimplementing TASS from first principles would be a large, separate research
program. It would also blur the boundary between a public interoperability layer
and the original BC model.

## Decision

`fresh-tipsy` will treat the `.tab` and `.taf` tables as the growth source. The
first engine selects the correct table and interpolates by age. It will not
reimplement TASS physics.

Product and economics layers may be reimplemented from documented logic and
validated against TIPSY/FAN$IER outputs.

## Consequences

Easier:

- extraction can start immediately;
- the growth engine is testable against known tables;
- the package stays small and auditable;
- provenance is direct.

Harder:

- unsupported species/site combinations cannot be extrapolated;
- product outputs still require a runtime or golden outputs;
- the package cannot claim to generate new TASS tables.

## Alternatives considered

- Reimplement TASS. Rejected: out of scope and not needed for the first release.
- Call a Windows GUI manually. Rejected: not testable or automatable.
- Use only TIPSY output CSVs. Rejected as the sole source: the database is a
  richer and more direct asset.

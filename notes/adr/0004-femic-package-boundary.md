# ADR 0004: Integrate with FEMIC through an optional package dependency

Status: proposed
Date: 2026-11-09
Issues: TBD

## Context

FEMIC already has TIPSY and FAN$IER concerns and local runtime glue. Copying
`fresh-tipsy` code into FEMIC would create two implementations and two sets of
provenance rules.

## Decision

`fresh-tipsy` is the source package for public TIPSY/FAN$IER table access,
growth queries, product recovery, and documented economics.

FEMIC consumes it through an optional dependency and a thin adapter. The adapter
passes provenance through and records the package version and data-manifest
hash. If the package is absent, FEMIC keeps its existing path.

## Consequences

Easier:

- one tested implementation;
- clear release and versioning;
- FEMIC can adopt incrementally;
- data and code provenance travel together.

Harder:

- package release and FEMIC release must be coordinated;
- the adapter needs a compatibility test;
- data assets must be available to FEMIC users.

## Alternatives considered

- Vendor the code into FEMIC. Rejected: duplicated implementation.
- Keep the package independent forever. Rejected: the user wants a usable
  dependency, not a museum piece.

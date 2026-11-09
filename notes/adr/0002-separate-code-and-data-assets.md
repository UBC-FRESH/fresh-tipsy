# ADR 0002: Separate code from government data assets

Status: proposed
Date: 2026-11-09
Issues: TBD

## Context

The TIPSY database is about 53 MB locally, and normalized tables could be much
larger. Raw government tables also have their own source and attribution. Putting
them in the Git repository would make the package heavy, obscure provenance, and
mix code review with data review.

## Decision

Track parsers, schemas, manifests, download instructions, and tiny fixtures.
Do not track raw databases or large normalized tables.

Publish normalized assets as release artifacts with a checksummed manifest. A
user can rebuild the assets from a local install using the CLI.

## Consequences

Easier:

- small repository and fast CI;
- clear code/data review;
- source attribution is explicit;
- data releases can be versioned independently.

Harder:

- a clean install needs a data-fetch or rebuild step;
- tests need small fixtures;
- release engineering must publish and verify data assets.

## Alternatives considered

- Commit the full database. Rejected: repository size and provenance.
- Use Git LFS. Deferred: it is an option if a small number of assets must be
  versioned, but it does not solve attribution.

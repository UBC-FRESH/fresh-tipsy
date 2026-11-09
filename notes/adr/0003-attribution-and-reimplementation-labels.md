# ADR 0003: Use explicit attribution and reimplementation labels

Status: proposed
Date: 2026-11-09
Issues: TBD

## Context

`fresh-tipsy` reads and reimplements parts of BC government models. The package
name is deliberately not a new model name. Users must be able to tell what came
from BC TIPSY/FAN$IER and what came from this package.

## Decision

Every public value carries:

```text
source
source version
source file or report
source SHA256 where possible
processing step
evidence level
citation
```

Evidence levels are `source_table`, `model_output`, `reimplemented`,
`validated_against`, `experimental`, and `unavailable`.

The README, CLI, API, web UI, and assistant all state that `fresh-tipsy` is an
interoperability layer, not the author of TIPSY/FAN$IER.

## Consequences

Easier:

- users can audit values;
- reimplemented logic is visible;
- model outputs are not mistaken for measured grades;
- citation is part of the data contract.

Harder:

- every output path must carry metadata;
- tests must assert provenance;
- the assistant needs a provenance tool and a prompt that refuses unsourced
  answers.

## Alternatives considered

- Cite only in the README. Rejected: per-value provenance is needed for science.
- Treat reimplementation as equivalent to the source. Rejected: it hides
  validation gaps.

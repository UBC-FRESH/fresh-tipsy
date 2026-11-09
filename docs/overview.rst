Overview
========

``fresh-tipsy`` is a public Python interoperability layer for BC TIPSY and
FAN$IER data tables. It is not a claim of authorship over the BC models or
their data.

The first release has four layers:

1. extract the TIPSY ``.tab`` and ``.taf`` database tables;
2. expose a typed catalog and growth query engine over the precomputed TASS
   yield surfaces;
3. expose TIPSY product columns and a documented FAN$IER-style economics
   layer;
4. provide a Typer CLI, FastAPI service, FRESH-style web UI, and bounded LLM
   assistant.

Read the plan in the repository:

- `program plan <https://github.com/UBC-FRESH/fresh-tipsy/blob/main/notes/plan/0001-program-plan.md>`_
- `data and provenance <https://github.com/UBC-FRESH/fresh-tipsy/blob/main/notes/plan/0002-data-provenance.md>`_
- `architecture <https://github.com/UBC-FRESH/fresh-tipsy/blob/main/notes/plan/0003-architecture.md>`_
- `validation and release <https://github.com/UBC-FRESH/fresh-tipsy/blob/main/notes/plan/0004-validation-release.md>`_

Source attribution
------------------

Every table and output records the BC source, version, file, SHA256, extraction
date, and citation. Reimplemented logic is labelled ``reimplemented`` and is
validated against TIPSY/FAN$IER outputs where possible.

Release material
----------------

- `release notes <https://github.com/UBC-FRESH/fresh-tipsy/blob/main/RELEASE_NOTES.md>`_
- `known gaps <https://github.com/UBC-FRESH/fresh-tipsy/blob/main/notes/reference/known-gaps.md>`_
- `citation instructions <https://github.com/UBC-FRESH/fresh-tipsy/blob/main/notes/reference/citation.md>`_

Non-goals
---------

- reimplementing TASS physics;
- claiming full TIPSY/FAN$IER parity in the first release;
- assigning measured BC log grades from model output;
- committing raw government databases or large data assets.

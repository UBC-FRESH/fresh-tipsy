# Package build validation (P6.2)

Date: 2026-11-09
Status: wheel and sdist build and clean-install smoke test complete
Scope: package build, packaged data, and manifest validation
Related: [`../../pyproject.toml`](../../pyproject.toml), [`testing.md`](testing.md), [`manifest-schema.md`](manifest-schema.md)

## Build

```bash
python -m build --outdir /tmp/fresh-tipsy-dist
```

Artifacts:

| Artifact | SHA-256 |
| --- | --- |
| `fresh_tipsy-0.1.0-py3-none-any.whl` | `8d56ffd7c416a5fa66065999ebee2422c7171b157eaa2684b29e0c6246b0494c` |
| `fresh_tipsy-0.1.0.tar.gz` | `029398a43870d1e1637ba6570fd92b90d153d6052a31157541cfb8cb77bfc471` |

The build emits no license deprecation warning after changing `project.license`
to the SPDX string `MIT`.

## Packaged contents

The wheel contains:

- `fresh_tipsy/tables/data/tab-taf-columns.csv`;
- `fresh_tipsy/tables/data/manifest-schema.json`;
- all web templates under `fresh_tipsy/web/templates/`;
- `fresh_tipsy/web/static/style.css`;
- the CLI entry point `fresh-tipsy = fresh_tipsy.cli:main`.

`tests/test_package_data.py` checks the table data and web assets through
`importlib.resources`.

## Clean-install smoke test

An isolated virtual environment installed the wheel and its declared runtime
dependencies, then ran:

```bash
fresh-tipsy --help
fresh-tipsy db validate \
  --catalog notes/reference/manifest-example.json \
  --source "$TIPSY_INSTALL" --json
fresh-tipsy curve query \
  --catalog notes/reference/manifest-example.json \
  --source "$TIPSY_INSTALL" \
  --species PLI --site-index 20 --age 36 --pnc N --stock-height 0.13 --json
```

Results:

- `fresh-tipsy --help` listed `db`, `curve`, `product`, and `econ`; exit 0.
- `db validate` returned `status: ok`, 2 assets, no errors.
- `curve query` returned `status: ok`, gross volume 746.0, and provenance
  `Database/pli0530N00.tab`.
- Packaged column map loaded 151 `.taf` columns.
- Packaged web template and static stylesheet were present.

## Known installation limits

- The minimal install includes Typer and jsonschema. Parquet normalization and
  `db extract` require the optional `parquet` extra (`pyarrow`).
- The web UI and HTTP API require the optional `api` extra (FastAPI, Jinja2, and
  uvicorn).
- The wheel does not include raw TIPSY tables or normalized assets.
- The package data is versioned with the package; a separate data release is
  P6.3.

## Reproduction

Use a clean virtual environment and a network-enabled package index:

```bash
python -m venv /tmp/fresh-tipsy-venv
/tmp/fresh-tipsy-venv/bin/pip install dist/fresh_tipsy-0.1.0-py3-none-any.whl
/tmp/fresh-tipsy-venv/bin/fresh-tipsy --help
```

No raw data or personal path is packaged.

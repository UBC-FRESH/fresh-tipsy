# Architecture plan

Date: 2026-11-09
Status: draft

## Package layout

```text
src/fresh_tipsy/
  __init__.py
  version.py
  provenance.py          source manifests, hashes, citations
  tables/
    formats.py           .tab/.taf grammar
    parsers.py           raw -> typed rows
    metadata.py          filename/header inference
    catalog.py           table index and search
    validate.py          counts, ranges, monotonicity
  curves/
    engine.py            species/site/PNC/stock-height selection
    interpolation.py     age interpolation
    models.py            typed request/result models
  products/
    schema.py            lumber, residue, log-grade, industrial-log columns
    recovery.py          product mix and mass balance
    lrf.py               public LRF fallback
  economics/
    prices.py            product price profiles
    costs.py             cost assumptions
    npv.py               discounting and sensitivity
    models.py            scenario request/result models
  api/
    service.py           shared typed service layer
    models.py            pydantic request/response models
  cli.py                 Typer application
  web/
    app.py               FastAPI application
    static/              FRESH-style UI
  agent/
    tools.py             bounded assistant tools
    prompts.py           provenance-first system prompts
```

## Core service layer

CLI, API, web, and assistant must call the same service functions. No interface
gets its own calculation path.

```python
class CurveQuery(BaseModel):
    species_code: str
    site_index: float
    age: int
    pnc: str | None = None
    stock_height_m: float | None = None


class CurvePoint(BaseModel):
    age: int
    volume_m3_ha: float
    height_m: float
    dbh_cm: float
    stems_per_ha: float
    provenance: Provenance
```

The first implementation should be simple: select the closest matching source
table, interpolate by age, return typed values plus provenance. Do not add
undocumented extrapolation.

## CLI

Typer commands:

```bash
fresh-tipsy db extract --source "$TIPSY_DATABASE" --out "$FRESH_TIPSY_CACHE"
fresh-tipsy db validate --catalog "$FRESH_TIPSY_CACHE/manifest.json"
fresh-tipsy db catalog --species PLI --site-index 20
fresh-tipsy curve query --species PLI --site-index 20 --age 80
fresh-tipsy product recover --input scenario.json
fresh-tipsy econ run --scenario scenario.json
fresh-tipsy serve --host 127.0.0.1 --port 8800
fresh-tipsy agent --help
```

Every command supports `--json` and writes machine-readable provenance.

## API

FastAPI endpoints:

```text
GET  /health
GET  /catalog
GET  /catalog/{table_id}
POST /curves/query
POST /products/recover
POST /economics/run
GET  /provenance/{asset_id}
```

Responses include:

```text
request
result
provenance
evidence
warnings
```

## Web UI

FRESH-style views:

- catalog browser with source metadata and checksum;
- curve explorer with species/site/age controls;
- product mix and residue table;
- economics scenario builder;
- provenance drawer on every result;
- assistant panel.

The UI must work without the assistant. The assistant is an additive interface
over the same service layer.

## LLM assistant

Bounded tools:

```text
search_catalog(query)
describe_table(table_id)
query_curve(species, site_index, age, ...)
compare_curves(queries)
recover_products(scenario)
run_economics(scenario)
get_provenance(asset_id)
```

Assistant rules:

- Every tool result carries provenance.
- The model may summarize, compare, and explain, but may not invent a table,
  column, coefficient, or result.
- If a query is unsupported, the tool returns a structured error; the assistant
  reports it.
- The assistant never claims a measured BC log grade or mill-specific recovery.

## Data access

- `fresh_tipsy.data` resolves assets from `FRESH_TIPSY_CACHE`, package extras, or
  a release manifest.
- Tests use tiny fixtures under `tests/data/`.
- Large assets are release artifacts, not repository content.

## FEMIC integration

The package exposes a small stable surface:

```python
from fresh_tipsy import query_curve, recover_products, run_economics
```

FEMIC integration should be optional:

```toml
[project.optional-dependencies]
fresh-tipsy = ["fresh-tipsy>=0.1"]
```

The integration layer:

- depends on the published package, not a copied module;
- passes provenance through to FEMIC outputs;
- records the `fresh-tipsy` version and data manifest hash;
- falls back to existing FEMIC tables if the package is absent.

## Non-negotiable boundaries

- No TASS reimplementation.
- No hidden default coefficients.
- No raw table commits.
- No grade claim from model output.
- No assistant answer without provenance.

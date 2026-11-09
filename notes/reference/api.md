# HTTP API and service layer (P5.2)

Date: 2026-11-09
Status: P5.2 complete
Scope: shared typed service envelope and FastAPI endpoints
Related: [`cli.md`](cli.md), [`testing.md`](testing.md), [`economics.md`](economics.md), [`../../src/fresh_tipsy/api/`](../../src/fresh_tipsy/api/)

## Install

The HTTP layer is optional:

```bash
pip install "fresh-tipsy[api]"
```

The service layer itself has no FastAPI dependency. CLI and API call the same
functions in `fresh_tipsy.api.service`.

## Application

```python
from pathlib import Path

from fresh_tipsy.api.app import create_app

app = create_app(
    catalog=Path("/data/fresh-tipsy/manifest.json"),
    source_root=Path("/opt/tipsy"),
)
```

If `catalog` is omitted, the application reads `FRESH_TIPSY_CATALOG`. If
`source_root` is omitted, the service reads `TIPSY_INSTALL`. A missing catalog
returns `not_configured` or `catalog_missing`; a missing source returns
`source_unavailable`.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Service health; no catalog required |
| `GET` | `/catalog` | Search tables by species, site, PNC, stock height, version, format, or text |
| `GET` | `/catalog/{asset_id}` | One table and its provenance |
| `POST` | `/curves/query` | Growth query |
| `POST` | `/products/recover` | Product recovery and mass-balance checks |
| `POST` | `/economics/run` | Explicit price/cost/NPV scenario |
| `GET` | `/provenance/{asset_id}` | Asset provenance |

`/products/recover` requires `format: "taf"`. A `.tab` request returns a
structured `product_failed` error.

## Response envelope

Every success and error response has the same shape:

```json
{
  "status": "ok",
  "request": {"query": {"species_code": "PLI", "site_index": 20, "age": 80}},
  "result": {"age": 80, "volume_merch_m3_ha": 0},
  "provenance": {"relative_path": "Database/pli0530N00.taf", "sha256": "..."},
  "evidence": "model_output",
  "warnings": [],
  "error": null
}
```

- `request` repeats the inputs.
- `result` is the typed result.
- `provenance` is the primary source table or asset.
- `evidence` is `source_table`, `model_output`, `reimplemented`, or another
  recorded label.
- `warnings` carries non-fatal gaps, such as unavailable mass-balance checks or
  missing prices.
- `error` is a structured `code` and `message` on failure.

Status codes:

- `400`: malformed service input.
- `404`: missing catalog asset.
- `422`: invalid request, unsupported query, product format, or economics
  scenario.
- `503`: no catalog or source configured.

## Service functions

The following functions are callable without HTTP:

```python
from fresh_tipsy.api.service import (
    asset_provenance,
    browse_catalog,
    health,
    parse_scenario,
    query_curve,
    recover_products,
    run_economics,
)
```

Each returns a `ServiceResponse` with the same envelope fields. The CLI uses
these functions for `curve query`, `product recover`, and `econ run`, so the
interfaces do not have separate calculation paths.

## Boundaries

- The API does not invent tables, prices, costs, or coefficients.
- Product values are TASS/SYLVER `model_output`, not measured field grades.
- Economics remains explicit-input, `reimplemented`, and unvalidated against
  FAN$IER.
- No raw table or normalized asset is written by API endpoints.
- The assistant and web UI are P5.3/P5.4 and are not required for the API.

# Web UI (P5.3)

Date: 2026-11-09
Status: P5.3 complete
Scope: server-rendered catalog, curve, product, and economics views
Related: [`api.md`](api.md), [`cli.md`](cli.md), [`testing.md`](testing.md), [`../../src/fresh_tipsy/web/`](../../src/fresh_tipsy/web/)

## Run

The web UI uses the optional API stack:

```bash
pip install "fresh-tipsy[api]"
export FRESH_TIPSY_CATALOG="$FRESH_TIPSY_CACHE/manifest.json"
export TIPSY_INSTALL="/opt/tipsy"
uvicorn fresh_tipsy.web.app:app --host 127.0.0.1 --port 8000
```

The UI is server-rendered with FastAPI and Jinja2. It has no JavaScript build
step, no LLM dependency, and no external network requirement.

## Views

| Path | View |
| --- | --- |
| `/ui` | Home and status |
| `/ui/catalog` | Catalog browser with filters and source checksum |
| `/ui/catalog/{asset_id}` | Table detail and full provenance |
| `/ui/curve` | Curve explorer with species, site, age, PNC, stock height, and format |
| `/ui/products` | Product groups, residues, totals, and mass-balance checks |
| `/ui/economics` | Explicit price, cost, discount, NPV, and site-value scenario builder |

Every result view includes a **Request and provenance** drawer containing the
request inputs, the primary source table and SHA-256, and any warnings. The
catalog list includes each table's source metadata and checksum.

## Economics form

The economics form requires an explicit discount rate. Price and cost are
optional explicit inputs; leaving the price blank produces a visible
`missing_price` gap rather than zero revenue. No default price or cost is
embedded.

The form supports one price line and one cost line for a first-pass scenario.
Use the CLI or API scenario JSON for multi-line price/cost scenarios.

## Boundaries

- The UI calls the shared service layer; it does not calculate curves,
  products, or economics itself.
- Product values are model output, not measured field grades.
- Economics is `reimplemented` and unvalidated against FAN$IER.
- Missing prices, unavailable mass-balance checks, and other gaps remain
  visible.
- No raw table or normalized asset is written by the UI.

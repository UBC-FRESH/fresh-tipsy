# Bounded assistant tools (P5.4)

Date: 2026-11-09
Status: P5.4 complete
Scope: deterministic tools and provenance-first prompt guidance
Related: [`api.md`](api.md), [`web.md`](web.md), [`testing.md`](testing.md), [`../../src/fresh_tipsy/agent/`](../../src/fresh_tipsy/agent/)

## Boundary

The assistant layer is a set of deterministic tools over the shared service
layer. It does not require a model, an API key, or an external network. An LLM
adapter is optional and can call the same tools.

Product values remain TASS/SYLVER `model_output`. Economics remains explicit
input, `reimplemented`, and unvalidated against FAN$IER. The tools never invent
a table, column, coefficient, price, cost, or grade.

## Toolbox

```python
from pathlib import Path

from fresh_tipsy.agent import ToolBox

tools = ToolBox(
    catalog=Path("/data/fresh-tipsy/manifest.json"),
    source_root=Path("/opt/tipsy"),
)
result = tools.query_curve({"species_code": "PLI", "site_index": 20, "age": 80, "format": "taf"})
print(result.as_dict())
```

Tools:

| Tool | Input | Result |
| --- | --- | --- |
| `search_catalog` | text and optional filters | matching tables and metadata |
| `describe_table` | `asset_id` | table metadata and provenance |
| `query_curve` | query mapping | curve metrics and provenance |
| `compare_curves` | list of query mappings | per-query results and partial errors |
| `recover_products` | query mapping | product groups, totals, checks, and provenance |
| `run_economics` | scenario mapping | revenue, NPV, gaps, and provenance |
| `get_provenance` | `asset_id` | source path, SHA-256, model, and citation |

Every result has `status`, `request`, `result`, `provenance`, `evidence`,
`warnings`, and `error`. A failed tool returns `status="error"` with a stable
`error.code`; it does not return fabricated values.

`recover_products` forces the requested format to `taf`.

## Prompt

`fresh_tipsy.agent.SYSTEM_PROMPT` tells an optional adapter to:

- use only the provided tools;
- identify the source table and query inputs;
- report errors and gaps instead of guessing;
- treat product values as model output, not measured grades;
- treat economics as unvalidated and explicit-input only;
- avoid mill-specific or measured-grade claims.

## Why no model dependency

The core package stays installable without an LLM SDK, API key, or network
access. Tests exercise the deterministic tools directly, so a model failure
cannot be mistaken for a data result.

## Gaps

- No live model adapter or prompt-evaluation suite is included.
- Assistant conversations are not persisted.
- Tool calls do not write data or change settings.
- No FAN$IER golden output or measured BC log grade is available.

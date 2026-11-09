# FEMIC integration (P6.4)

Date: 2026-11-09
Status: fresh-tipsy adapter and contract complete; FEMIC repository change pending separate approval
Scope: optional dependency, thin adapter, provenance pass-through, and skip-safe test
Related: [`../../src/fresh_tipsy/integrations/femic.py`](../../src/fresh_tipsy/integrations/femic.py), [`../adr/0004-femic-package-boundary.md`](../adr/0004-femic-package-boundary.md), [`api.md`](api.md), [`release-assets.md`](release-assets.md)

## Optional dependency for FEMIC

Add `fresh-tipsy` as an optional dependency, not a vendored copy:

```toml
[project.optional-dependencies]
fresh-tipsy = ["fresh-tipsy>=0.1"]
```

FEMIC keeps its existing path when the extra is absent. A release should pin the
same data-manifest version and record the package version in output metadata.

## Thin adapter

FEMIC can call the adapter from `fresh_tipsy.integrations`:

```python
from pathlib import Path

from fresh_tipsy.integrations import query_growth, recover_products, run_economics

result = query_growth(
    Path("/data/fresh-tipsy/manifest.json"),
    Path("/opt/tipsy"),
    {"species_code": "PLI", "site_index": 20, "age": 80, "pnc": "N"},
)
payload = result.as_dict()
```

The payload contains:

```text
status
result
provenance
evidence
warnings
error
fresh_tipsy_version
data_manifest_sha256
```

`recover_products` forces `.taf`, and `run_economics` accepts the shared
scenario mapping. `asset_provenance` returns one catalog asset with its source
path and checksum.

FEMIC should store `fresh_tipsy_version`, `data_manifest_sha256`, and
`provenance` with its output. It should not copy the source table or relabel
model output as a measured field grade.

## Skip-safe test

In FEMIC:

```python
import pytest

fresh_tipsy = pytest.importorskip("fresh_tipsy")
from fresh_tipsy.integrations import query_growth
```

Use a tiny synthetic manifest fixture for the call. When the optional package or
data is absent, the test skips; a skip is not a pass. The fresh-tipsy adapter
tests cover success, product/economics wrappers, provenance, and structured
errors.

## Back-link documentation

The FEMIC change should add:

- the optional `fresh-tipsy` dependency and version floor;
- a short adapter description linking to this note;
- the provenance/version/hash fields in output docs;
- a changelog entry for the optional integration.

That change is not applied here because it is an external repository change
requiring separate approval. The current FEMIC worktree has unrelated changes
and must not be overwritten.

## Boundaries

- No `fresh-tipsy` module is copied into FEMIC.
- No raw TIPSY table is committed or bundled.
- FAN$IER remains unparsed and unvalidated.
- The adapter does not claim full FEMIC parity or a measured grade.
- The adapter is optional; a missing package is a clean skip, not an error.

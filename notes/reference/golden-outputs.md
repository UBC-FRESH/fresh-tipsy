# Golden output and fixture inventory (P1.5)

Date: 2026-11-09
Status: redistribution unresolved for source data; checksum-only path selected
Scope: tiny fixtures and golden output candidates
Related: [`source-inventory.md`](source-inventory.md), [`tab-taf-grammar.md`](tab-taf-grammar.md), [`manifest-schema.md`](manifest-schema.md), [`golden-outputs.csv`](golden-outputs.csv), [`../../tests/data/fixtures/synthetic/README.md`](../../tests/data/fixtures/synthetic/README.md)

## Redistribution decision

The TIPSY Use Policy (June 2023) and the TIPSY 4.5 release note grant use of the
software and describe the data, but neither states redistribution terms for the
database. No explicit permission to redistribute the raw `.tab`, `.taf`, or
`.fns` files was found.

Following the P1.5 fallback, the project stores **checksums and reproduction
commands only** for real source data. No raw BC table is committed. The only
committed `.tab`/`.taf` files are the clearly marked synthetic parser fixtures
under `tests/data/fixtures/synthetic/`.

## Synthetic parser fixtures

| File | Size | SHA-256 | Purpose |
| --- | ---: | --- | --- |
| `tests/data/fixtures/synthetic/syn0010N02.tab` | 557 bytes | `038121b1afa939d16cebce93494d7abffc375dc53b259c649bcd59efc6ca9898` | 22-field `.tab`, two run blocks, PCT boundary |
| `tests/data/fixtures/synthetic/syn0010N02.taf` | 2,363 bytes | `4888ec98d0113e2a9ee1ac35ffad63e2a0dbe585f5e933f786c1aad53512786f` | 151-field `.taf`, two run blocks, PCT boundary |

- The fixtures are synthetic, not BC data, and not for golden validation.
- They use LF line endings; the real source files use CRLF. The parser must
  handle both.
- `tests/test_fixtures.py` checks the field counts, the two run blocks, the PCT
  block, and the synthetic marker.
- The fixture directory README repeats the synthetic warning.

## Candidate source fixtures

These are the best tiny real-source candidates. They are not committed.

| Candidate | File | Size | SHA-256 | Status |
| --- | --- | ---: | --- | --- |
| Compact table | `Database/pli0530N00.tab` | 27,317 bytes | `55bfaa37745819e66d41a66349b72617b0a094e1041a11070f9b641c3b3827aa` | checksum only |
| Full table | `Database/pli0530N00.taf` | 124,361 bytes | `569d57639c86b7360b7a577599c37688b38c2060a8f8202ed82548de7238581d` | checksum only |

Both files are from TIPSY 4.5, source build `v3.01.13W (Feb 2017 - Jul 2021)`, database `Ministry Standard Database, February 2022`. They are the `Lodgepole Pine`, site 5-30, PNC `N`, stock height 0.13 m pair.

## Golden output inventory

| ID | Kind | Source | Status | Notes |
| --- | --- | --- | --- | --- |
| `golden-tipsy-pli0530n00-tab` | source table | TIPSY 4.5 | checksum only | Compact table; 22 fields, 16 runs, 276 data rows |
| `golden-tipsy-pli0530n00-taf` | source table | TIPSY 4.5 | checksum only | Full table; 151 fields, 16 runs, 276 data rows |
| `golden-tipsy-pli0530n00-products` | model output | TIPSY 4.5 `.taf` | available in `.taf` | Product columns 2-10 and 68-150; LRF is derived in P4 |
| `golden-fansier-sample-fns` | sample project | FAN$IER | located, not validated | `Samples/sample.fns`; no economic run captured |
| `golden-femic-tsr` | golden output | FEMIC | not captured | P3.4 confirmed no output; the comparison remains a gap |
| `golden-tipsy-custom-runtime` | model output | TIPSY 4.5 runtime | unavailable | Custom output blocked by the .NET 4.8/Wine failure |

The machine-readable inventory is in [`golden-outputs.csv`](golden-outputs.csv).

## What the golden inventory proves

- The `.tab` and `.taf` pair is a valid golden candidate for the growth, stock, mortality, biomass, and product columns.
- The `.taf` product columns are precomputed model output; a separate runtime capture is not needed for this table.
- Fresh-tipsy cannot claim a validated TIPSY custom output, a FAN$IER economic output, or a FEMIC TSR comparison yet. Those remain gaps.

## Reproduction and verification

Set the source roots through environment variables. Do not hard-code a host path.

```bash
TIPSY_DATABASE="${TIPSY_DATABASE:-$TIPSY_INSTALL/Database}"
sha256sum "$TIPSY_DATABASE/pli0530N00.tab"
sha256sum "$TIPSY_DATABASE/pli0530N00.taf"
```

The checksums must match the P1.1 table manifest:

```bash
python - <<'PY'
import csv, hashlib, os

def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()

root = os.environ["TIPSY_DATABASE"]
for name in ("pli0530N00.tab", "pli0530N00.taf"):
    path = os.path.join(root, name)
    print(name, os.path.getsize(path), sha256(path))
PY
```

Synthetic fixture checks run without a TIPSY install:

```bash
python -m pytest tests/test_fixtures.py
```

Real-source tests must skip when `TIPSY_DATABASE` is unset. They must never
commit the source table.

## Gaps

- No redistributable real `.tab`/`.taf` excerpt was committed because redistribution terms are unclear.
- The TIPSY custom runtime fails under Wine, so custom output goldens are unavailable.
- No FAN$IER economic run is captured. The sample `.fns` is located but not validated.
- No FEMIC TSR output was located in this phase.

These gaps are recorded in the data manifest and must not be filled with guessed
values.

## Attribution

The candidate source files are the work of the Province of British Columbia.
Cite TIPSY 4.5 and the relative source path. The synthetic fixtures are original
test data and are not BC source data.

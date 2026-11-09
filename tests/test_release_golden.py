"""Release golden regression against representative TIPSY tables."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from fresh_tipsy.curves import CurveEngine, CurveQuery, compare_metric
from fresh_tipsy.tables import (
    PairTable,
    TableCatalog,
    build_tab_manifest_entry,
    build_taf_manifest_entry,
    parse_pair,
    parse_tab_file,
)

_CASES = (
    ("pli0530N00", "PLI", 20.0, 36.0, "N", 0.13),
    ("fdc1050N00", "FDC", 30.0, 36.0, "N", None),
    ("at 1032C00", "AT", 20.0, 45.0, "C", None),
    ("fdi0535C00", "FDI", 20.0, 49.0, "C", 0.21),
)


def _manifest(pair: PairTable, source_root: Path) -> dict[str, object]:
    """Build a two-asset manifest for one pair."""
    return {
        "manifest_version": "1.2.0",
        "generated_at_utc": "2026-11-09T00:00:00Z",
        "extractor": {"name": "fresh-tipsy", "version": "0.1.0", "parser_version": 1},
        "source_install": {"model": "TIPSY", "version": "4.5", "install_env": "TIPSY_INSTALL"},
        "assets": [
            build_tab_manifest_entry(pair.tab, source_root),
            build_taf_manifest_entry(pair.taf, source_root),
        ],
    }


def test_four_species_golden_regression() -> None:
    """Exact TIPSY ages and product mass balance pass for four species."""
    database = os.environ.get("TIPSY_DATABASE")
    if database is None:
        pytest.skip("TIPSY_DATABASE is not set")
    root = Path(database)
    for stem, species, site, age, pnc, stock_height in _CASES:
        pair = parse_pair(root / f"{stem}.tab")
        engine = CurveEngine(
            TableCatalog.from_manifest_data(_manifest(pair, root)),
            source_root=root,
        )
        table = parse_tab_file(root / f"{stem}.tab")
        row = next(
            row
            for block in table.blocks
            if block.treatment is None
            for row in block.rows
            if row.age == age
        )
        query = CurveQuery(
            species,
            site,
            age=age,
            pnc=pnc,
            stock_height_m=stock_height,
            format="tab",
        )
        comparison = compare_metric(
            engine.metric(query, "volume_gross"),
            float(row.fields[2]),
            tolerance=1e-9,
        )
        assert comparison.passed, (stem, comparison.as_dict())
        product_query = CurveQuery(
            species,
            site,
            age=age,
            pnc=pnc,
            stock_height_m=stock_height,
            format="taf",
        )
        recovery = engine.products(product_query)
        assert all(check.status != "fail" for check in recovery.checks), stem
        assert recovery.provenance.evidence == "model_output"

"""Real-source product regression checks."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from fresh_tipsy.curves import CurveEngine, CurveQuery
from fresh_tipsy.tables import (
    TableCatalog,
    build_taf_manifest_entry,
    parse_taf_file,
)


def test_real_pli_product_mass_balance() -> None:
    """PLI product goldens pass every available mass-balance check."""
    database = os.environ.get("TIPSY_DATABASE")
    if database is None:
        pytest.skip("TIPSY_DATABASE is not set")
    database_root = Path(database)
    install_root = database_root.parent
    table = parse_taf_file(database_root / "pli0530N00.taf")
    manifest: dict[str, object] = {
        "manifest_version": "1.2.0",
        "generated_at_utc": "2026-11-09T00:00:00Z",
        "extractor": {"name": "fresh-tipsy", "version": "0.1.0", "parser_version": 1},
        "source_install": {"model": "TIPSY", "version": "4.5", "install_env": "TIPSY_INSTALL"},
        "assets": [build_taf_manifest_entry(table, install_root)],
    }
    engine = CurveEngine(
        TableCatalog.from_manifest_data(manifest),
        source_root=install_root,
    )
    for age in (36.0, 55.0, 91.0):
        recovery = engine.products(
            CurveQuery(
                "PLI",
                20.0,
                age=age,
                pnc="N",
                stock_height_m=0.13,
                format="taf",
            )
        )
        assert recovery.provenance.evidence == "model_output"
        assert all(check.status != "fail" for check in recovery.checks)
        crosscheck = next(
            check for check in recovery.checks if check.name == "lumber_2_or_better_vs_graded"
        )
        assert crosscheck.status == "pass", crosscheck.as_dict()
        assert recovery.totals.lumber_2_or_better_bf_ha is not None
        assert recovery.totals.graded_bf_ha is not None
        assert recovery.totals.logs_m3_ha is not None

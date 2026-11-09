"""Tests for product recovery and mass-balance checks."""

from __future__ import annotations

from pathlib import Path

import pytest

from fresh_tipsy.curves import CurveEngine, CurveQuery
from fresh_tipsy.products import (
    MassBalanceError,
    ProductUnavailableError,
    recover_products,
)
from fresh_tipsy.tables import (
    TableCatalog,
    build_tab_manifest_entry,
    build_taf_manifest_entry,
    parse_pair,
)

_PRODUCT_POSITIONS: tuple[int, ...] = (
    *range(2, 11),
    *range(68, 76),
    *range(91, 131),
    *range(131, 151),
)


def _header() -> list[str]:
    """Build a synthetic header for a one-row pair."""
    return [
        "[TASS SPECIES]",
        "DatabaseTitle=Synthetic product fixture",
        "File=syn0010N00",
        "SpeciesName=Synthetic species",
        "Source=synthetic",
        "Code=SYN",
        "SiteFrom=0",
        "SiteTo=10",
        "TASSsiteIndex=0",
        "TASSsiteSpecies=",
        "PNC=N",
        "",
        "[RUN,1000,0,0]",
        "",
    ]


def _tab_row() -> list[str]:
    """Build a compact row for the product pair."""
    fields = ["0"] * 22
    fields[0] = "5"
    fields[1] = "10"
    fields[2] = "100"
    return fields


def _taf_row(
    *,
    lumber_2x4: float = 10.0,
    product_values: bool = True,
    all_grades_fallback: bool = False,
) -> list[str]:
    """Build a full row with known product values."""
    fields = ["0"] * 151
    fields[0] = "5"
    fields[1] = "10"
    fields[2] = str(lumber_2x4)
    if product_values:
        fields[3] = "20"
        fields[4] = "30"
        fields[5] = "40"
        for offset, value in enumerate(("1", "2", "3", "4", "5"), start=6):
            fields[offset] = value
        for offset, value in enumerate(("1", "2", "3", "4", "5", "6", "7", "8"), start=68):
            fields[offset] = value
        fields[91] = "10"
        fields[92] = "20"
        fields[93] = "30"
        fields[94] = "20" if all_grades_fallback else "40"
        if all_grades_fallback:
            fields[103] = "20"
    else:
        for position in _PRODUCT_POSITIONS:
            fields[position] = ""
    return fields


def _engine(
    tmp_path: Path,
    *,
    lumber_2x4: float = 10.0,
    product_values: bool = True,
    all_grades_fallback: bool = False,
) -> CurveEngine:
    """Build an engine for the synthetic product pair."""
    (tmp_path / "syn0010N00.tab").write_text(
        "\n".join([*_header(), "\t".join(_tab_row())]), encoding="ascii"
    )
    (tmp_path / "syn0010N00.taf").write_text(
        "\n".join(
            [
                *_header(),
                "\t".join(
                    _taf_row(
                        lumber_2x4=lumber_2x4,
                        product_values=product_values,
                        all_grades_fallback=all_grades_fallback,
                    )
                ),
            ]
        ),
        encoding="ascii",
    )
    pair = parse_pair(tmp_path / "syn0010N00.tab")
    manifest: dict[str, object] = {
        "manifest_version": "1.2.0",
        "generated_at_utc": "2026-11-09T00:00:00Z",
        "extractor": {"name": "fresh-tipsy", "version": "0.1.0", "parser_version": 1},
        "source_install": {"model": "TIPSY", "version": "4.5", "install_env": "TIPSY_INSTALL"},
        "assets": [
            build_tab_manifest_entry(pair.tab, tmp_path),
            build_taf_manifest_entry(pair.taf, tmp_path),
        ],
    }
    return CurveEngine(TableCatalog.from_manifest_data(manifest), source_root=tmp_path)


def _query() -> CurveQuery:
    """Return the product query."""
    return CurveQuery("SYN", 5.0, age=5.0, format="taf")


def test_recover_products_groups_and_totals(tmp_path: Path) -> None:
    """Product recovery exposes all groups, totals, and passing checks."""
    recovery = _engine(tmp_path).products(_query())
    assert recovery.age == 5.0
    assert recovery.scenario == "untreated"
    assert recovery.provenance.evidence == "model_output"
    assert len(recovery.lumber_2_or_better) == 4
    assert len(recovery.residues) == 5
    assert len(recovery.log_grades) == 8
    assert len(recovery.graded_lumber) == 20
    assert len(recovery.degraded_lumber) == 20
    assert len(recovery.industrial_logs) == 20
    assert all(item.field.evidence == "model_output" for item in recovery.graded_lumber)
    assert recovery.totals.lumber_2_or_better_bf_ha == 100.0
    assert recovery.totals.graded_bf_ha == 100.0
    assert recovery.totals.degraded_bf_ha == 0.0
    assert recovery.totals.logs_m3_ha == 36.0
    assert recovery.totals.residues_odt_ha == 15.0
    assert recovery.totals.industrial_m3_ha == 0.0
    checks = {check.name: check for check in recovery.checks}
    assert checks["lumber_2_or_better"].status == "pass"
    assert checks["lumber_graded"].status == "pass"
    assert checks["lumber_degraded"].status == "pass"
    assert checks["logs"].status == "pass"
    assert checks["residues"].status == "unavailable"
    assert checks["lumber_2_or_better_vs_graded"].status == "pass"
    assert checks["lumber_2_or_better_vs_graded"].independent
    data = recovery.as_dict()
    totals = data["totals"]
    assert isinstance(totals, dict)
    assert totals["graded_bf_ha"] == 100.0


def test_product_mass_balance_failure_is_hard(tmp_path: Path) -> None:
    """A failed #2 & Better cross-check raises unless strict is disabled."""
    engine = _engine(tmp_path, lumber_2x4=11.0)
    with pytest.raises(MassBalanceError, match="lumber_2_or_better_vs_graded"):
        engine.products(_query())
    recovery = recover_products(engine.query(_query()), strict=False)
    checks = {check.name: check for check in recovery.checks}
    failed = checks["lumber_2_or_better_vs_graded"]
    assert failed.status == "fail"
    assert failed.difference == 1.0


def test_product_mass_balance_all_grade_fallback(tmp_path: Path) -> None:
    """Tables that put every grade in #2 & Better pass the cross-check."""
    recovery = _engine(tmp_path, all_grades_fallback=True).products(_query())
    check = next(check for check in recovery.checks if check.name == "lumber_2_or_better_vs_graded")
    assert check.status == "pass"
    assert check.component_sum == 100.0
    assert "all five grades" in check.note


def test_product_recovery_requires_taf(tmp_path: Path) -> None:
    """A compact table cannot answer product queries."""
    engine = _engine(tmp_path)
    query = CurveQuery("SYN", 5.0, age=5.0)
    with pytest.raises(ProductUnavailableError, match=r"\.taf"):
        engine.products(query)


def test_product_recovery_blank_products(tmp_path: Path) -> None:
    """Blank product columns produce unavailable checks, not failures."""
    recovery = _engine(tmp_path, product_values=False).products(_query())
    assert recovery.totals.lumber_2_or_better_bf_ha is None
    assert recovery.totals.residues_odt_ha is None
    assert all(check.status == "unavailable" for check in recovery.checks)

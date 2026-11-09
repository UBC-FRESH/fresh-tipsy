"""Contract tests for the typed product schema."""

from __future__ import annotations

from collections import Counter

import pytest

from fresh_tipsy.products import (
    MASS_BALANCE_RULES,
    PRODUCT_FIELDS,
    PRODUCT_TOTALS,
    ProductGroup,
    product_field,
)
from fresh_tipsy.tables import load_columns


def test_product_field_count_and_groups() -> None:
    """The schema covers 77 fields in six groups."""
    assert len(PRODUCT_FIELDS) == 77
    counts = Counter(field.group for field in PRODUCT_FIELDS)
    assert counts == {
        ProductGroup.LUMBER_2_OR_BETTER: 4,
        ProductGroup.RESIDUE: 5,
        ProductGroup.LOG_GRADE: 8,
        ProductGroup.LUMBER_GRADED: 20,
        ProductGroup.LUMBER_DEGRADED: 20,
        ProductGroup.INDUSTRIAL_LOG: 20,
    }


def test_product_positions_match_column_map() -> None:
    """Every product field matches the packaged `.taf` column map."""
    columns = {column.name: column for column in load_columns("taf")}
    names = [field.name for field in PRODUCT_FIELDS]
    positions = [field.position for field in PRODUCT_FIELDS]
    assert len(set(names)) == 77
    assert len(set(positions)) == 77
    for field in PRODUCT_FIELDS:
        column = columns[field.name]
        assert field.position == column.position
        assert field.units == column.units
        assert field.evidence == "model_output"


def test_graded_and_degraded_dimensions() -> None:
    """Each lumber grade has all four dimensions."""
    graded = [field for field in PRODUCT_FIELDS if field.group is ProductGroup.LUMBER_GRADED]
    degraded = [field for field in PRODUCT_FIELDS if field.group is ProductGroup.LUMBER_DEGRADED]
    assert {field.grade for field in graded} == {"SS", "1", "2", "3", "4"}
    assert {field.dimension for field in graded} == {"2x4", "2x6", "2x8", "2x10"}
    assert {field.grade for field in degraded} == {"SS", "1", "2", "3", "4"}
    assert {field.dimension for field in degraded} == {"2x4", "2x6", "2x8", "2x10"}


def test_product_totals_and_mass_balance_rules() -> None:
    """The aggregates and reconciliation rules are complete."""
    assert len(PRODUCT_TOTALS) == 7
    rules = {rule.name: rule for rule in MASS_BALANCE_RULES}
    assert set(rules) == {
        "lumber_2_or_better",
        "lumber_graded",
        "lumber_degraded",
        "logs",
        "residues",
    }
    assert len(rules["lumber_2_or_better"].component_fields) == 4
    assert len(rules["lumber_graded"].component_fields) == 20
    assert len(rules["lumber_degraded"].component_fields) == 20
    assert len(rules["logs"].component_fields) == 8
    assert len(rules["residues"].component_fields) == 5
    assert rules["residues"].total_field is None
    totals = {total.name for total in PRODUCT_TOTALS}
    assert rules["lumber_2_or_better"].total_field in totals
    assert rules["lumber_graded"].total_field in totals
    assert rules["lumber_degraded"].total_field in totals
    assert rules["logs"].total_field in totals


def test_product_field_lookup() -> None:
    """A product field can be looked up by name."""
    field = product_field("Lumber_Graded_1_2x6")
    assert field.group is ProductGroup.LUMBER_GRADED
    assert field.grade == "1"
    assert field.dimension == "2x6"
    with pytest.raises(KeyError, match="unknown product field"):
        product_field("not_a_product")

"""Tests for packaged data and web assets."""

from __future__ import annotations

from importlib.resources import files

from fresh_tipsy.tables.columns import load_columns


def test_packaged_table_data() -> None:
    """The column map and manifest schema are inside the package."""
    package = files("fresh_tipsy.tables").joinpath("data")
    assert package.joinpath("tab-taf-columns.csv").is_file()
    assert package.joinpath("manifest-schema.json").is_file()
    assert len(load_columns("taf")) == 151
    assert len(load_columns("tab")) == 22


def test_packaged_web_assets() -> None:
    """Templates and static assets are inside the package."""
    templates = files("fresh_tipsy.web").joinpath("templates")
    static = files("fresh_tipsy.web").joinpath("static")
    for name in (
        "base.html",
        "catalog.html",
        "curve.html",
        "product.html",
        "economics.html",
    ):
        assert templates.joinpath(name).is_file()
    assert static.joinpath("style.css").is_file()

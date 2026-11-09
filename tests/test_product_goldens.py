"""Checksum and structure tests for the product golden inventory."""

from __future__ import annotations

import csv
import hashlib
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "notes" / "reference" / "product-goldens.csv"


def _rows() -> list[dict[str, str]]:
    """Load the product golden inventory."""
    with INVENTORY.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_product_golden_inventory_structure() -> None:
    """The inventory names candidates, gaps, and query inputs."""
    rows = _rows()
    assert len(rows) == 7
    checksums = [row for row in rows if row["status"] == "checksum_only"]
    assert len(checksums) == 4
    assert {row["source_model"] for row in checksums} == {"TIPSY"}
    assert all(row["query_inputs"] for row in checksums)
    assert all(row["product_groups"] for row in checksums)
    gaps = [row for row in rows if row["status"] in {"unavailable", "located_not_validated"}]
    assert len(gaps) == 3
    assert all(row["evidence"] == "unavailable" for row in gaps)


def _sha256(path: Path) -> str:
    """Return a file SHA-256."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_product_golden_checksums() -> None:
    """Checksum-only candidates match their recorded source files."""
    tipsy_install = os.environ.get("TIPSY_INSTALL")
    if tipsy_install is None:
        database = os.environ.get("TIPSY_DATABASE")
        tipsy_install = str(Path(database).parent) if database else None
    fansier_root = os.environ.get("FANSIER_INSTALL")
    checked = 0
    for row in _rows():
        if not row["relative_path"] or not row["sha256"]:
            continue
        if row["source_model"] == "TIPSY":
            if tipsy_install is None:
                continue
            root = Path(tipsy_install)
        else:
            if fansier_root is None:
                continue
            root = Path(fansier_root)
        path = root / row["relative_path"]
        assert path.is_file(), path
        assert path.stat().st_size == int(row["size_bytes"])
        assert _sha256(path) == row["sha256"]
        checked += 1
    if tipsy_install is None and fansier_root is None:
        pytest.skip("TIPSY_DATABASE and FANSIER_INSTALL are not set")
    assert checked >= 1

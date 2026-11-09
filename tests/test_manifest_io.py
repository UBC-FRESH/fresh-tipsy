"""Tests for manifest construction, serialization, and file checks."""

from __future__ import annotations

import json
from pathlib import Path

from fresh_tipsy.tables import build_tab_manifest_entry, build_taf_manifest_entry, parse_pair
from fresh_tipsy.tables.manifest_io import (
    build_manifest,
    load_manifest,
    load_schema,
    validate_manifest_data,
    validate_manifest_files,
    write_manifest,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "data" / "fixtures" / "synthetic"
FIXTURE_TAB = FIXTURES / "syn0010N02.tab"
REFERENCE_SCHEMA = ROOT / "notes" / "reference" / "manifest-schema.json"


def _manifest() -> dict[str, object]:
    """Build a valid synthetic manifest."""
    pair = parse_pair(FIXTURE_TAB)
    return build_manifest(
        [
            build_tab_manifest_entry(pair.tab, FIXTURES),
            build_taf_manifest_entry(pair.taf, FIXTURES),
        ],
        {"model": "TIPSY", "version": "4.5", "install_env": "TIPSY_INSTALL"},
        "test",
        generated_at_utc="2026-11-09T00:00:00Z",
    )


def test_packaged_schema_matches_reference() -> None:
    """The package schema matches the committed reference schema."""
    reference = json.loads(REFERENCE_SCHEMA.read_text(encoding="utf-8"))
    assert load_schema() == reference


def test_build_manifest_validates() -> None:
    """A built manifest validates against the packaged schema."""
    assert validate_manifest_data(_manifest()) == []


def test_write_and_load_manifest(tmp_path: Path) -> None:
    """A manifest round-trips through deterministic JSON."""
    manifest = _manifest()
    path = write_manifest(manifest, tmp_path / "manifest.json")
    assert load_manifest(path) == manifest
    first = path.read_text(encoding="utf-8")
    write_manifest(manifest, path)
    assert path.read_text(encoding="utf-8") == first


def test_validate_files_reports_missing_artifact(tmp_path: Path) -> None:
    """A missing released artifact is a file error."""
    manifest = _manifest()
    assets = manifest["assets"]
    assert isinstance(assets, list)
    assets.append(
        {
            "id": "normalized-missing",
            "artifact": {
                "relative_path": "missing.csv",
                "sha256": "0" * 64,
                "size_bytes": 1,
            },
        }
    )
    errors, warnings = validate_manifest_files(manifest, tmp_path)
    assert warnings == ["source checks skipped: pass --source to verify raw files"]
    assert any("does not exist" in error for error in errors)

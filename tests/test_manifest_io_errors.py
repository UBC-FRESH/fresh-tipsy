"""Error-path tests for manifest I/O and file validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from fresh_tipsy.tables import build_tab_manifest_entry, build_taf_manifest_entry, parse_pair
from fresh_tipsy.tables.manifest_io import (
    ManifestError,
    build_manifest,
    load_manifest,
    validate_manifest_data,
    validate_manifest_files,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "data" / "fixtures" / "synthetic"
FIXTURE_TAB = FIXTURES / "syn0010N02.tab"


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


def test_build_manifest_default_timestamp() -> None:
    """The default timestamp is UTC with a Z suffix."""
    manifest = build_manifest(
        [],
        {"model": "TIPSY", "version": "4.5", "install_env": "TIPSY_INSTALL"},
        "test",
    )
    timestamp = manifest["generated_at_utc"]
    assert isinstance(timestamp, str)
    assert timestamp.endswith("Z")


def test_load_manifest_invalid_json(tmp_path: Path) -> None:
    """Invalid JSON raises a manifest error."""
    path = tmp_path / "manifest.json"
    path.write_text("{bad", encoding="utf-8")
    with pytest.raises(ManifestError, match="not valid JSON"):
        load_manifest(path)


def test_load_manifest_non_object(tmp_path: Path) -> None:
    """A non-object manifest raises a manifest error."""
    path = tmp_path / "manifest.json"
    path.write_text("[]", encoding="utf-8")
    with pytest.raises(ManifestError, match="not an object"):
        load_manifest(path)


def test_validate_manifest_data_reports_errors() -> None:
    """An invalid manifest produces schema errors."""
    assert validate_manifest_data({"manifest_version": "1.2.0"}) != []


def test_validate_manifest_files_assets_not_list() -> None:
    """A non-list assets field is a file error."""
    errors, _ = validate_manifest_files({"assets": {}}, Path("."))
    assert errors == ["assets must be a list"]


def test_validate_manifest_files_rejects_non_object_asset(tmp_path: Path) -> None:
    """A non-object asset is a manifest error."""
    with pytest.raises(ManifestError, match="must be an object"):
        validate_manifest_files({"assets": [1]}, tmp_path)


def test_validate_manifest_files_duplicate_ids(tmp_path: Path) -> None:
    """Duplicate asset IDs are reported."""
    manifest = _manifest()
    assets = manifest["assets"]
    assert isinstance(assets, list)
    assets.append({"id": assets[0]["id"]})
    errors, _ = validate_manifest_files(manifest, tmp_path)
    assert any("duplicate asset id" in error for error in errors)


def test_validate_manifest_files_path_escape(tmp_path: Path) -> None:
    """An artifact path that escapes the root is rejected."""
    manifest = _manifest()
    assets = manifest["assets"]
    assert isinstance(assets, list)
    assets.append(
        {
            "id": "escape",
            "artifact": {
                "relative_path": "../outside.csv",
                "sha256": "0" * 64,
                "size_bytes": 1,
            },
        }
    )
    errors, _ = validate_manifest_files(manifest, tmp_path)
    assert any("escapes" in error for error in errors)


def test_validate_manifest_files_size_and_hash(tmp_path: Path) -> None:
    """Size and checksum mismatches are reported."""
    path = tmp_path / "data.csv"
    path.write_text("data", encoding="utf-8")
    manifest: dict[str, object] = {
        "assets": [
            {
                "id": "bad-size",
                "artifact": {
                    "relative_path": "data.csv",
                    "sha256": "0" * 64,
                    "size_bytes": 999,
                },
            }
        ]
    }
    errors, _ = validate_manifest_files(manifest, tmp_path)
    assert any("size mismatch" in error for error in errors)
    assert any("sha256 mismatch" in error for error in errors)


def test_validate_manifest_files_checks_sources(tmp_path: Path) -> None:
    """Source files are checked when a source root is supplied."""
    manifest = _manifest()
    errors, warnings = validate_manifest_files(manifest, tmp_path, FIXTURES)
    assert errors == []
    assert warnings == []
    errors, _ = validate_manifest_files(manifest, tmp_path, tmp_path / "missing")
    assert any("does not exist" in error for error in errors)


def test_validate_manifest_files_source_mismatch(tmp_path: Path) -> None:
    """A modified source file produces size and checksum errors."""
    source = tmp_path / "source"
    source.mkdir()
    (source / "syn0010N02.tab").write_text("changed", encoding="ascii")
    (source / "syn0010N02.taf").write_text("changed", encoding="ascii")
    manifest = _manifest()
    errors, _ = validate_manifest_files(manifest, tmp_path, source)
    assert any("size mismatch" in error for error in errors)
    assert any("sha256 mismatch" in error for error in errors)


def test_manifest_json_helpers_are_stable(tmp_path: Path) -> None:
    """A manifest JSON write is deterministic and readable."""
    manifest = _manifest()
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    assert load_manifest(path) == manifest

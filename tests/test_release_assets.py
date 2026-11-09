"""Tests for release asset validation."""

from __future__ import annotations

import hashlib
from pathlib import Path

from check_release_assets import check_release

ROOT = Path(__file__).resolve().parents[1]


def _errors(summary: dict[str, object]) -> list[str]:
    """Return summary errors with a concrete type."""
    errors = summary["errors"]
    assert isinstance(errors, list)
    return [str(error) for error in errors]


def _checksums(directory: Path, names: list[str]) -> None:
    """Write checksums for selected files."""
    lines = []
    for name in names:
        digest = hashlib.sha256((directory / name).read_bytes()).hexdigest()
        lines.append(f"{digest}  {name}")
    (directory / "checksums.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_release_assets_pass(tmp_path: Path) -> None:
    """A checksummed package artifact passes."""
    (tmp_path / "fresh.whl").write_bytes(b"wheel")
    _checksums(tmp_path, ["fresh.whl"])
    summary = check_release(tmp_path)
    assert summary["status"] == "ok"
    assert summary["assets"] == 2


def test_release_assets_reject_raw_data(tmp_path: Path) -> None:
    """Raw TIPSY tables are rejected even with a valid checksum."""
    (tmp_path / "table.tab").write_bytes(b"raw")
    _checksums(tmp_path, ["table.tab"])
    summary = check_release(tmp_path)
    assert summary["status"] == "error"
    assert any("raw table" in error for error in _errors(summary))


def test_release_assets_reject_bad_checksum(tmp_path: Path) -> None:
    """A checksum mismatch is an error."""
    (tmp_path / "fresh.whl").write_bytes(b"wheel")
    (tmp_path / "checksums.txt").write_text("0" * 64 + "  fresh.whl\n", encoding="utf-8")
    summary = check_release(tmp_path)
    assert any("checksum mismatch" in error for error in _errors(summary))


def test_release_assets_validate_manifest(tmp_path: Path) -> None:
    """The optional data manifest is schema-validated."""
    (tmp_path / "fresh.whl").write_bytes(b"wheel")
    _checksums(tmp_path, ["fresh.whl"])
    summary = check_release(tmp_path, ROOT / "notes/reference/manifest-example.json")
    assert summary["status"] == "ok"
    bad = tmp_path / "bad-manifest.json"
    bad.write_text('{"assets": []}', encoding="utf-8")
    summary = check_release(tmp_path, bad)
    assert any("manifest" in error for error in _errors(summary))


def test_release_assets_missing_inputs(tmp_path: Path) -> None:
    """Missing directories and checksum files fail explicitly."""
    summary = check_release(tmp_path / "missing")
    assert summary["status"] == "error"
    summary = check_release(tmp_path)
    assert any("checksums.txt" in error for error in _errors(summary))

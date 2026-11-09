"""Manifest construction, serialization, and validation."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from datetime import UTC, datetime
from importlib import resources
from pathlib import Path
from typing import Final

import jsonschema

from fresh_tipsy.version import __version__

MANIFEST_VERSION: Final[str] = "1.2.0"
PARSER_VERSION: Final[int] = 1


class ManifestError(ValueError):
    """Raised when a manifest cannot be built, read, or validated."""


def load_schema() -> dict[str, object]:
    """Load the packaged manifest JSON Schema.

    Returns
    -------
    dict of str to object
        The JSON Schema object.

    Raises
    ------
    ManifestError
        When the packaged schema is missing or not a JSON object.
    """
    text = (
        resources.files("fresh_tipsy.tables")
        .joinpath("data/manifest-schema.json")
        .read_text(encoding="utf-8")
    )
    data = json.loads(text)
    if not isinstance(data, dict):
        message = "packaged manifest schema is not an object"
        raise ManifestError(message)
    return {str(key): value for key, value in data.items()}


def build_manifest(
    assets: Sequence[dict[str, object]],
    source_install: dict[str, object],
    command: str,
    gaps: Sequence[dict[str, object]] = (),
    generated_at_utc: str | None = None,
) -> dict[str, object]:
    """Build a manifest envelope.

    Parameters
    ----------
    assets : sequence of dict of str to object
        Manifest asset entries.
    source_install : dict of str to object
        Source installation metadata.
    command : str
        Command that produced the assets.
    gaps : sequence of dict of str to object, optional
        Known gaps.
    generated_at_utc : str or None, optional
        UTC timestamp. Defaults to the current time.

    Returns
    -------
    dict of str to object
        Manifest envelope.
    """
    timestamp = generated_at_utc or (
        datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    )
    return {
        "manifest_version": MANIFEST_VERSION,
        "generated_at_utc": timestamp,
        "extractor": {
            "name": "fresh-tipsy",
            "version": __version__,
            "parser_version": PARSER_VERSION,
            "command": command,
        },
        "source_install": source_install,
        "assets": list(assets),
        "gaps": list(gaps),
    }


def write_manifest(manifest: dict[str, object], path: Path) -> Path:
    """Write a manifest as deterministic JSON.

    Parameters
    ----------
    manifest : dict of str to object
        Manifest envelope.
    path : Path
        Output path.

    Returns
    -------
    Path
        The written path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path


def load_manifest(path: Path) -> dict[str, object]:
    """Read a manifest file.

    Parameters
    ----------
    path : Path
        Manifest path.

    Returns
    -------
    dict of str to object
        Parsed manifest.

    Raises
    ------
    ManifestError
        When the file is not valid JSON or not an object.
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        message = f"manifest is not valid JSON: {path}"
        raise ManifestError(message) from exc
    if not isinstance(data, dict):
        message = f"manifest is not an object: {path}"
        raise ManifestError(message)
    return {str(key): value for key, value in data.items()}


def validate_manifest_data(manifest: dict[str, object]) -> list[str]:
    """Validate a manifest against the packaged schema.

    Parameters
    ----------
    manifest : dict of str to object
        Manifest envelope.

    Returns
    -------
    list of str
        Schema errors, empty when valid.
    """
    validator = jsonschema.Draft202012Validator(load_schema())
    errors: list[str] = []
    for error in sorted(validator.iter_errors(manifest), key=lambda item: list(item.path)):
        location = "/".join(str(part) for part in error.path) or "<root>"
        errors.append(f"{location}: {error.message}")
    return errors


def _mapping(value: object, label: str) -> dict[str, object]:
    """Convert a JSON object to a mapping.

    Parameters
    ----------
    value : object
        Candidate value.
    label : str
        Location label.

    Returns
    -------
    dict of str to object
        String-keyed mapping.

    Raises
    ------
    ManifestError
        When the value is not an object.
    """
    if not isinstance(value, dict):
        message = f"{label} must be an object"
        raise ManifestError(message)
    return {str(key): item for key, item in value.items()}


def _sha256(path: Path) -> str:
    """Return a file SHA-256.

    Parameters
    ----------
    path : Path
        File to hash.

    Returns
    -------
    str
        Lowercase SHA-256.
    """
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _check_file(
    root: Path,
    relative_path: str,
    sha256: str,
    size_bytes: int,
    label: str,
    errors: list[str],
) -> None:
    """Check one file's existence, size, and checksum.

    Parameters
    ----------
    root : Path
        Root directory.
    relative_path : str
        Relative path.
    sha256 : str
        Expected SHA-256.
    size_bytes : int
        Expected size.
    label : str
        Location label for errors.
    errors : list of str
        Error accumulator.
    """
    root_resolved = root.resolve()
    candidate = (root / relative_path).resolve()
    if not candidate.is_relative_to(root_resolved):
        errors.append(f"{label}: path escapes {root}")
        return
    if not candidate.is_file():
        errors.append(f"{label}: file does not exist: {relative_path}")
        return
    if candidate.stat().st_size != size_bytes:
        errors.append(f"{label}: size mismatch: {relative_path}")
    if _sha256(candidate) != sha256:
        errors.append(f"{label}: sha256 mismatch: {relative_path}")


def validate_manifest_files(
    manifest: dict[str, object],
    root: Path,
    source_root: Path | None = None,
) -> tuple[list[str], list[str]]:
    """Validate artifact and source files referenced by a manifest.

    Parameters
    ----------
    manifest : dict of str to object
        Manifest envelope.
    root : Path
        Root for released artifacts.
    source_root : Path or None, optional
        Source install root. When omitted, source checks are skipped.

    Returns
    -------
    tuple of (list of str, list of str)
        File errors and warnings.

    Raises
    ------
    ManifestError
        When the manifest structure is not an object where expected.
    """
    errors: list[str] = []
    warnings: list[str] = []
    assets = manifest.get("assets")
    if not isinstance(assets, list):
        return (["assets must be a list"], warnings)
    seen: set[str] = set()
    for index, value in enumerate(assets):
        asset = _mapping(value, f"assets[{index}]")
        asset_id = asset.get("id")
        if isinstance(asset_id, str):
            if asset_id in seen:
                errors.append(f"assets[{index}]: duplicate asset id {asset_id!r}")
            seen.add(asset_id)
        artifact = asset.get("artifact")
        if isinstance(artifact, dict):
            artifact_map = _mapping(artifact, f"assets[{index}].artifact")
            relative = artifact_map.get("relative_path")
            digest = artifact_map.get("sha256")
            size = artifact_map.get("size_bytes")
            if isinstance(relative, str) and isinstance(digest, str) and isinstance(size, int):
                _check_file(root, relative, digest, size, f"assets[{index}].artifact", errors)
        source = asset.get("source")
        if isinstance(source, dict):
            if source_root is None:
                if not any(warning.startswith("source checks skipped") for warning in warnings):
                    warnings.append("source checks skipped: pass --source to verify raw files")
                continue
            source_map = _mapping(source, f"assets[{index}].source")
            relative = source_map.get("relative_path")
            digest = source_map.get("sha256")
            size = source_map.get("size_bytes")
            if isinstance(relative, str) and isinstance(digest, str) and isinstance(size, int):
                _check_file(source_root, relative, digest, size, f"assets[{index}].source", errors)
    return (errors, warnings)

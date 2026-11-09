"""Validate a fresh-tipsy release asset directory."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from fresh_tipsy.tables.manifest_io import validate_manifest_data

_RAW_SUFFIXES = {".tab", ".taf", ".fns", ".brs", ".rgm", ".tip"}


def _sha256(path: Path) -> str:
    """Return a file SHA-256.

    Parameters
    ----------
    path : Path
        File path.

    Returns
    -------
    str
        Lowercase hex digest.
    """
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_checksums(path: Path) -> dict[str, str]:
    """Read a sha256sum-style file.

    Parameters
    ----------
    path : Path
        Checksum file.

    Returns
    -------
    dict of str to str
        File name to digest.

    Raises
    ------
    ValueError
        When a line is malformed.
    """
    checksums: dict[str, str] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            message = f"checksums.txt line {line_number} is malformed"
            raise ValueError(message)
        digest, name = parts
        checksums[name.strip()] = digest.strip().lower()
    return checksums


def check_release(directory: Path, manifest: Path | None = None) -> dict[str, object]:
    """Check release assets for checksums, raw data, and manifest validity.

    Parameters
    ----------
    directory : Path
        Release asset directory.
    manifest : Path or None, optional
        Data manifest to validate.

    Returns
    -------
    dict of str to object
        Validation summary.
    """
    errors: list[str] = []
    if not directory.is_dir():
        return {"status": "error", "errors": [f"release directory does not exist: {directory}"]}
    assets = sorted(path for path in directory.iterdir() if path.is_file())
    raw = [path.name for path in assets if path.suffix.lower() in _RAW_SUFFIXES]
    if raw:
        errors.append("raw table assets are not allowed: " + ", ".join(raw))
    checksum_path = directory / "checksums.txt"
    checks: dict[str, str] = {}
    if not checksum_path.is_file():
        errors.append("checksums.txt is missing")
    else:
        try:
            checks = _read_checksums(checksum_path)
        except (OSError, ValueError) as exc:
            errors.append(str(exc))
        if not checks:
            errors.append("checksums.txt has no entries")
        for name, expected in checks.items():
            path = directory / name
            if not path.is_file():
                errors.append(f"checksum references a missing file: {name}")
                continue
            actual = _sha256(path)
            if actual != expected:
                errors.append(f"checksum mismatch: {name}")
    manifest_path = manifest
    if manifest_path is None and (directory / "manifest.json").is_file():
        manifest_path = directory / "manifest.json"
    if manifest_path is not None:
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"manifest cannot be read: {exc}")
        else:
            if not isinstance(data, dict):
                errors.append("manifest must be a JSON object")
            else:
                errors.extend(validate_manifest_data(data))
    return {
        "status": "ok" if not errors else "error",
        "directory": str(directory),
        "assets": len(assets),
        "checksums": len(checks),
        "errors": errors,
    }


def main() -> None:
    """Run the release asset validator."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="Release asset directory.")
    parser.add_argument("--manifest", type=Path, help="Optional data manifest.")
    parser.add_argument("--json", action="store_true", help="Print JSON.")
    args = parser.parse_args()
    summary = check_release(args.directory, args.manifest)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Status: {summary['status']}")
        errors = summary["errors"]
        assert isinstance(errors, list)
        for error in errors:
            print(f"Error: {error}")
    raise SystemExit(0 if summary["status"] == "ok" else 1)


if __name__ == "__main__":
    main()

"""Optional FEMIC integration helpers."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from fresh_tipsy.api.service import (
    ServiceError,
    ServiceResponse,
    parse_curve_query,
    parse_scenario,
    query_curve,
)
from fresh_tipsy.api.service import (
    asset_provenance as service_asset_provenance,
)
from fresh_tipsy.api.service import (
    recover_products as service_recover_products,
)
from fresh_tipsy.api.service import (
    run_economics as service_run_economics,
)
from fresh_tipsy.version import __version__


def _sha256(path: Path) -> str | None:
    """Return a manifest SHA-256 when available.

    Parameters
    ----------
    path : Path
        Manifest path.

    Returns
    -------
    str or None
        Digest, or ``None`` when the file is unavailable.
    """
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class FemicResult:
    """A provenance-preserving result for FEMIC.

    Parameters
    ----------
    status : str
        ``"ok"`` or ``"error"``.
    result : dict of str to object or None
        Query result.
    provenance : dict of str to object or None
        Source provenance.
    evidence : str or None
        Evidence label.
    warnings : tuple of dict
        Non-fatal gaps.
    error : dict of str to str or None
        Structured error.
    package_version : str
        Installed fresh-tipsy version.
    manifest_sha256 : str or None
        Data manifest SHA-256, when available.
    """

    status: str
    result: dict[str, object] | None
    provenance: dict[str, object] | None
    evidence: str | None
    warnings: tuple[dict[str, str], ...]
    error: dict[str, str] | None
    package_version: str
    manifest_sha256: str | None

    def as_dict(self) -> dict[str, object]:
        """Return a FEMIC-ready mapping.

        Returns
        -------
        dict of str to object
            Result fields.
        """
        return {
            "status": self.status,
            "result": self.result,
            "provenance": self.provenance,
            "evidence": self.evidence,
            "warnings": list(self.warnings),
            "error": self.error,
            "fresh_tipsy_version": self.package_version,
            "data_manifest_sha256": self.manifest_sha256,
        }


def _adapt(response: ServiceResponse, catalog: Path) -> FemicResult:
    """Wrap a service response for FEMIC."""
    return FemicResult(
        status=response.status,
        result=response.result,
        provenance=response.provenance,
        evidence=response.evidence,
        warnings=tuple(warning.as_dict() for warning in response.warnings),
        error=None if response.error is None else response.error.as_dict(),
        package_version=__version__,
        manifest_sha256=_sha256(catalog),
    )


def _error(error: Exception, catalog: Path) -> FemicResult:
    """Wrap a service error for FEMIC."""
    code = error.code if isinstance(error, ServiceError) else "invalid_request"
    return FemicResult(
        status="error",
        result=None,
        provenance=None,
        evidence=None,
        warnings=(),
        error={"code": code, "message": str(error)},
        package_version=__version__,
        manifest_sha256=_sha256(catalog),
    )


def query_growth(
    catalog: Path,
    source_root: Path | None,
    query: dict[str, object],
) -> FemicResult:
    """Query growth for a FEMIC adapter.

    Parameters
    ----------
    catalog : Path
        Manifest path.
    source_root : Path or None
        TIPSY install root.
    query : dict of str to object
        Growth query fields.

    Returns
    -------
    FemicResult
        Result with package version and manifest hash.
    """
    try:
        parsed = parse_curve_query(query)
        return _adapt(query_curve(catalog, source_root, parsed), catalog)
    except (ServiceError, ValueError, OSError) as exc:
        return _error(exc, catalog)


def recover_products(
    catalog: Path,
    source_root: Path | None,
    query: dict[str, object],
) -> FemicResult:
    """Recover products for a FEMIC adapter.

    Parameters
    ----------
    catalog : Path
        Manifest path.
    source_root : Path or None
        TIPSY install root.
    query : dict of str to object
        Product query fields.

    Returns
    -------
    FemicResult
        Result with package version and manifest hash.
    """
    try:
        parsed = parse_curve_query({**query, "format": "taf"})
        return _adapt(service_recover_products(catalog, source_root, parsed), catalog)
    except (ServiceError, ValueError, OSError) as exc:
        return _error(exc, catalog)


def run_economics(
    catalog: Path,
    source_root: Path | None,
    scenario: dict[str, object],
) -> FemicResult:
    """Run economics for a FEMIC adapter.

    Parameters
    ----------
    catalog : Path
        Manifest path.
    source_root : Path or None
        TIPSY install root.
    scenario : dict of str to object
        Scenario fields.

    Returns
    -------
    FemicResult
        Result with package version and manifest hash.
    """
    try:
        parsed = parse_scenario(scenario)
        return _adapt(service_run_economics(catalog, source_root, parsed), catalog)
    except (ServiceError, ValueError, OSError) as exc:
        return _error(exc, catalog)


def asset_provenance(catalog: Path, asset_id: str) -> FemicResult:
    """Return asset provenance for a FEMIC adapter.

    Parameters
    ----------
    catalog : Path
        Manifest path.
    asset_id : str
        Stable asset ID.

    Returns
    -------
    FemicResult
        Result with package version and manifest hash.
    """
    try:
        return _adapt(service_asset_provenance(catalog, asset_id), catalog)
    except (ServiceError, ValueError, OSError) as exc:
        return _error(exc, catalog)

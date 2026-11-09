"""Filename metadata for TIPSY database tables."""

from __future__ import annotations

import re
from dataclasses import dataclass

from fresh_tipsy.tables.errors import TableFormatError

_FILENAME_RE: re.Pattern[str] = re.compile(
    r"^(?P<species>[a-z]{2,3})\s?"
    r"(?P<site_from>\d{2})(?P<site_to>\d{2})"
    r"(?P<pnc>[CNP])"
    r"(?P<pct>\d{2})"
    r"(?P<ct>\d{2})?$"
)


@dataclass(frozen=True)
class FilenameMetadata:
    """Metadata encoded in a TIPSY table filename.

    Parameters
    ----------
    species_code : str
        Uppercase species code.
    site_from : int
        Minimum site index.
    site_to : int
        Maximum site index.
    pnc : str
        Planted, natural, or clumped code.
    pct_code : int
        PCT code from the filename; ``0`` when absent.
    ct_code : int or None
        Commercial-thinning code, or ``None`` when absent.
    """

    species_code: str
    site_from: int
    site_to: int
    pnc: str
    pct_code: int
    ct_code: int | None


def parse_filename(stem: str) -> FilenameMetadata:
    """Parse a TIPSY table filename stem into metadata.

    Parameters
    ----------
    stem : str
        Filename without its extension.

    Returns
    -------
    FilenameMetadata
        The metadata encoded in the filename.

    Raises
    ------
    TableFormatError
        When the stem does not match the documented filename grammar or the
        site range is inverted.
    """
    match = _FILENAME_RE.fullmatch(stem)
    if match is None:
        message = f"filename does not match the TIPSY grammar: {stem!r}"
        raise TableFormatError(message)
    site_from = int(match.group("site_from"))
    site_to = int(match.group("site_to"))
    if site_from > site_to:
        message = f"filename site range is inverted: {stem!r}"
        raise TableFormatError(message)
    ct_raw = match.group("ct")
    return FilenameMetadata(
        species_code=match.group("species").upper(),
        site_from=site_from,
        site_to=site_to,
        pnc=match.group("pnc"),
        pct_code=int(match.group("pct")),
        ct_code=int(ct_raw) if ct_raw is not None else None,
    )


def slugify(value: str) -> str:
    """Convert a value into a stable lowercase slug.

    Parameters
    ----------
    value : str
        Text to slugify.

    Returns
    -------
    str
        Lowercase letters, digits, and hyphens.
    """
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")

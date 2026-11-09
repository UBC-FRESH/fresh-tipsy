"""Errors raised by the TIPSY table readers."""

from __future__ import annotations


class TableFormatError(ValueError):
    """Raised when a TIPSY table does not match the documented grammar."""

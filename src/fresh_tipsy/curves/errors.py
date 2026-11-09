"""Errors raised by the growth query engine."""

from __future__ import annotations


class UnsupportedQueryError(ValueError):
    """Raised when no source table can answer a growth query."""

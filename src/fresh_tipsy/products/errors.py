"""Errors raised by the product recovery layer."""

from __future__ import annotations


class ProductUnavailableError(ValueError):
    """Raised when a source format does not contain product columns."""


class MassBalanceError(ValueError):
    """Raised when a product total does not reconcile with its components."""

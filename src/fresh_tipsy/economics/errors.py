"""Errors raised by the economics layer."""

from __future__ import annotations


class EconomicsError(ValueError):
    """Base class for explicit economics failures."""


class InvalidEconomicsInputError(EconomicsError):
    """Raised when an economic input is malformed or out of range."""


class MissingPriceError(EconomicsError):
    """Raised when a product has no matching price entry."""


class AmbiguousPriceError(EconomicsError):
    """Raised when more than one equally specific price matches a product."""


class UnitMismatchError(EconomicsError):
    """Raised when a price unit cannot be applied to a product quantity unit."""

"""Reimplemented product economics with explicit assumptions."""

from __future__ import annotations

from fresh_tipsy.economics.engine import evaluate_economics, evaluate_sensitivity
from fresh_tipsy.economics.errors import (
    AmbiguousPriceError,
    EconomicsError,
    InvalidEconomicsInputError,
    MissingPriceError,
    UnitMismatchError,
)
from fresh_tipsy.economics.models import (
    CashFlow,
    CostCategory,
    CostEntry,
    CostLine,
    DiscountAssumptions,
    EconomicGap,
    EconomicResult,
    EconomicsRequest,
    PriceBook,
    PriceEntry,
    PriceKey,
    RevenueLine,
    SensitivityCase,
    SensitivityCaseResult,
    SensitivityResult,
    fansier_sensitivity_cases,
)

__all__ = [
    "AmbiguousPriceError",
    "CashFlow",
    "CostCategory",
    "CostEntry",
    "CostLine",
    "DiscountAssumptions",
    "EconomicGap",
    "EconomicResult",
    "EconomicsError",
    "EconomicsRequest",
    "InvalidEconomicsInputError",
    "MissingPriceError",
    "PriceBook",
    "PriceEntry",
    "PriceKey",
    "RevenueLine",
    "SensitivityCase",
    "SensitivityCaseResult",
    "SensitivityResult",
    "UnitMismatchError",
    "evaluate_economics",
    "evaluate_sensitivity",
    "fansier_sensitivity_cases",
]

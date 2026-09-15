"""Shared validation helpers for the simulation models.

The project represents rates and proportions as decimal fractions throughout
the model layer (for example, ``0.023`` means 2.3%).
"""

from __future__ import annotations

import math
from numbers import Integral, Real


def finite_number(name: str, value: Real) -> float:
    """Return *value* as a finite float or raise a descriptive ``ValueError``."""
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a real number.")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite.")
    return result


def fraction(name: str, value: Real) -> float:
    """Validate a decimal fraction in the inclusive range 0 to 1."""
    result = finite_number(name, value)
    if not 0.0 <= result <= 1.0:
        raise ValueError(f"{name} must be between 0 and 1 inclusive.")
    return result


def non_negative(name: str, value: Real) -> float:
    """Validate a finite number greater than or equal to zero."""
    result = finite_number(name, value)
    if result < 0.0:
        raise ValueError(f"{name} must be non-negative.")
    return result


def integer_at_least(name: str, value: Integral, minimum: int) -> int:
    """Validate an integer with an inclusive lower bound."""
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise ValueError(f"{name} must be an integer.")
    result = int(value)
    if result < minimum:
        raise ValueError(f"{name} must be at least {minimum}.")
    return result

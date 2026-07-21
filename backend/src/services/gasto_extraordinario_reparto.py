"""Pure functions for splitting monthly extraordinary expenses among escribanos."""

from __future__ import annotations

from decimal import ROUND_DOWN, Decimal

_CENTS = Decimal("0.01")
_ZERO = Decimal("0.00")


def reparto_equitativo(total: Decimal, cantidad_escribanos: int) -> list[Decimal]:
    """Split *total* into equal shares; remainder cents go to the last share.

    The caller MUST sort escribanos alphabetically by name before mapping shares
    so the remainder is assigned to the last escribano in alphabetical order (FR-011).
    """
    if cantidad_escribanos <= 0:
        return []

    if total < _ZERO:
        raise ValueError("total must be non-negative")

    total = total.quantize(_CENTS)
    if cantidad_escribanos == 1:
        return [total]

    base = (total / cantidad_escribanos).quantize(_CENTS, rounding=ROUND_DOWN)
    cuotas = [base] * cantidad_escribanos
    remanente = total - base * cantidad_escribanos
    if remanente != _ZERO:
        cuotas[-1] = (cuotas[-1] + remanente).quantize(_CENTS)
    return cuotas

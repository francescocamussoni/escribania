"""Pure functions for client payment balance (saldo) calculations.

All functions are side-effect free and operate on Decimal values (P6).
"""

from decimal import Decimal

_ZERO = Decimal("0.00")
_CENTS = Decimal("0.01")


def calc_saldo(costo_total: Decimal, total_pagado: Decimal) -> Decimal:
    """Return outstanding balance, floored at zero."""
    saldo = (costo_total - total_pagado).quantize(_CENTS)
    return saldo if saldo > _ZERO else _ZERO


def can_close(saldo_pendiente: Decimal) -> bool:
    """Return True only when there is no outstanding client balance."""
    return saldo_pendiente == _ZERO


def is_sobrepago(costo_total: Decimal, total_pagado: Decimal) -> bool:
    """Return True when total paid exceeds current invoice total."""
    return total_pagado > costo_total

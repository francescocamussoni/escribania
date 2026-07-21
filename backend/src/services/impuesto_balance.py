"""Pure functions for impuestos balance and escritura close eligibility (P6)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Sequence
from uuid import UUID

_ZERO = Decimal("0.00")
_CENTS = Decimal("0.01")


@dataclass(frozen=True)
class ImpuestoPagoEstado:
    impuesto_id: UUID
    tipo: str
    tiene_pago_cliente: bool
    tiene_pago_escribania: bool


def calc_balance(
    montos_cliente: Sequence[Decimal],
    montos_escribania: Sequence[Decimal],
) -> Decimal:
    """Accumulated balance: Σ pagos cliente − Σ pagos escribanía."""
    total_cliente = sum(montos_cliente, start=_ZERO)
    total_escribania = sum(montos_escribania, start=_ZERO)
    return (total_cliente - total_escribania).quantize(_CENTS)


def impuestos_pendientes(
    impuestos: Sequence[ImpuestoPagoEstado],
) -> list[dict[str, Any]]:
    """Return impuestos missing client and/or escribanía payments."""
    pendientes: list[dict[str, Any]] = []
    for impuesto in impuestos:
        falta_cliente = not impuesto.tiene_pago_cliente
        falta_escribania = not impuesto.tiene_pago_escribania
        if not falta_cliente and not falta_escribania:
            continue
        pendientes.append({
            "impuesto_id": impuesto.impuesto_id,
            "tipo": impuesto.tipo,
            "falta_cliente": falta_cliente,
            "falta_escribania": falta_escribania,
        })
    return pendientes


def can_close_impuestos(
    balance: Decimal,
    pendientes: Sequence[dict[str, Any]],
) -> bool:
    """True when balance is zero and every loaded impuesto has both payments."""
    return balance == _ZERO and len(pendientes) == 0

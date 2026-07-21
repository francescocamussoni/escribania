from decimal import Decimal
from typing import Any


class EscrituraNotFoundError(Exception):
    """Raised when an escritura does not exist."""


class EscrituraClosedError(Exception):
    """Raised when mutating a closed escritura."""


class EscrituraSaldoPendienteError(Exception):
    """Raised when closing an escritura with outstanding client balance."""

    def __init__(self, saldo_pendiente: Decimal) -> None:
        self.saldo_pendiente = Decimal(saldo_pendiente)
        super().__init__(
            f"Cannot close escritura with outstanding balance: {self.saldo_pendiente}"
        )


class EscrituraImpuestosBalanceError(Exception):
    """Raised when closing an escritura with non-zero impuestos balance (FR-025)."""

    code = "impuestos_balance_pendiente"

    def __init__(self, balance: Decimal) -> None:
        self.balance = Decimal(balance)
        super().__init__(
            f"Cannot close escritura with impuestos balance: {self.balance}"
        )


class EscrituraImpuestosPagosPendientesError(Exception):
    """Raised when impuestos lack client or escribanía payments (FR-025b)."""

    code = "impuestos_pagos_pendientes"

    def __init__(self, impuestos_pendientes: list[dict[str, Any]]) -> None:
        self.impuestos_pendientes = list(impuestos_pendientes)
        super().__init__(
            "Cannot close escritura: impuestos with incomplete payments: "
            f"{len(self.impuestos_pendientes)}"
        )

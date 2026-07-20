from decimal import Decimal


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

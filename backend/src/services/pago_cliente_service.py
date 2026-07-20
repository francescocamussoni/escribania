from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from events.publisher import publish
from models.escritura import Escritura, EstadoEscritura
from models.pago_cliente import PagoCliente
from schemas.pago_cliente import PagoClienteInput
from services.escritura_errors import EscrituraClosedError, EscrituraNotFoundError
from services.pago_saldo import calc_saldo


class PagoClienteExcesoSaldoError(Exception):
    """Raised when a client payment exceeds the outstanding balance."""

    def __init__(self, saldo_pendiente: Decimal) -> None:
        self.saldo_pendiente = Decimal(saldo_pendiente)
        super().__init__(f"Pago exceeds saldo pendiente: {self.saldo_pendiente}")


def _ensure_open(escritura: Escritura) -> None:
    if escritura.estado == EstadoEscritura.CERRADA:
        raise EscrituraClosedError("Cannot modify a closed escritura")


async def _get_escritura_or_404(session: AsyncSession, escritura_id: uuid.UUID) -> Escritura:
    escritura = await session.scalar(
        select(Escritura)
        .options(selectinload(Escritura.factura))
        .where(Escritura.id == escritura_id)
    )
    if escritura is None:
        raise EscrituraNotFoundError("Escritura not found")
    return escritura


async def sum_pagos(session: AsyncSession, escritura_id: uuid.UUID) -> Decimal:
    total = await session.scalar(
        select(func.coalesce(func.sum(PagoCliente.monto), 0)).where(
            PagoCliente.escritura_id == escritura_id
        )
    )
    return Decimal(str(total))


async def create_pago(
    session: AsyncSession,
    escritura_id: uuid.UUID,
    payload: PagoClienteInput,
) -> PagoCliente:
    escritura = await _get_escritura_or_404(session, escritura_id)
    _ensure_open(escritura)

    if escritura.factura is None:
        raise RuntimeError("Escritura has no factura principal")

    costo_total = escritura.factura.total_factura
    total_pagado = await sum_pagos(session, escritura_id)
    saldo_pendiente = calc_saldo(costo_total, total_pagado)

    if payload.monto > saldo_pendiente:
        raise PagoClienteExcesoSaldoError(saldo_pendiente)

    pago = PagoCliente(
        id=uuid.uuid4(),
        escritura_id=escritura_id,
        monto=payload.monto,
        fecha=payload.fecha,
        concepto=payload.concepto,
    )
    session.add(pago)
    await session.commit()
    await session.refresh(pago)

    escritura_id_str = str(escritura_id)
    await publish(
        "pago_cliente.created",
        {"escritura_id": escritura_id_str, "pago_id": str(pago.id)},
    )
    await publish("liquidacion.updated", {"escritura_id": escritura_id_str})
    await publish("libros_updated", {"escritura_id": escritura_id_str})

    return pago

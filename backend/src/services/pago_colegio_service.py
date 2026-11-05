from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from events.publisher import publish
from models.escritura import Escritura, EstadoEscritura
from models.pago_colegio import PagoColegio, TipoPagoEscribania
from schemas.pago_colegio import PagoColegioInput
from services.escritura_errors import EscrituraClosedError, EscrituraNotFoundError


def _ensure_open(escritura: Escritura) -> None:
    if escritura.estado == EstadoEscritura.CERRADA:
        raise EscrituraClosedError("Cannot modify a closed escritura")


async def _get_escritura_or_404(session: AsyncSession, escritura_id: uuid.UUID) -> Escritura:
    escritura = await session.scalar(select(Escritura).where(Escritura.id == escritura_id))
    if escritura is None:
        raise EscrituraNotFoundError("Escritura not found")
    return escritura


async def sum_pagos(session: AsyncSession, escritura_id: uuid.UUID) -> Decimal:
    total = await session.scalar(
        select(func.coalesce(func.sum(PagoColegio.monto), 0)).where(
            PagoColegio.escritura_id == escritura_id
        )
    )
    return Decimal(str(total))


async def sum_pagos_colegio(session: AsyncSession, escritura_id: uuid.UUID) -> Decimal:
    total = await session.scalar(
        select(func.coalesce(func.sum(PagoColegio.monto), 0)).where(
            PagoColegio.escritura_id == escritura_id,
            PagoColegio.tipo == TipoPagoEscribania.COLEGIO,
        )
    )
    return Decimal(str(total)).quantize(Decimal("0.01"))


async def sum_pagos_impuestos(session: AsyncSession, escritura_id: uuid.UUID) -> Decimal:
    """Deprecated alias — use sum_pagos_colegio."""
    return await sum_pagos_colegio(session, escritura_id)


async def create_pago(
    session: AsyncSession,
    escritura_id: uuid.UUID,
    payload: PagoColegioInput,
) -> PagoColegio:
    escritura = await _get_escritura_or_404(session, escritura_id)
    _ensure_open(escritura)

    pago = PagoColegio(
        id=uuid.uuid4(),
        escritura_id=escritura_id,
        monto=payload.monto,
        fecha=payload.fecha,
        concepto=payload.concepto,
        tipo=payload.tipo,
    )
    session.add(pago)
    await session.commit()
    await session.refresh(pago)

    escritura_id_str = str(escritura_id)
    await publish(
        "pago_colegio.created",
        {"escritura_id": escritura_id_str, "pago_id": str(pago.id)},
    )
    await publish("libros_updated", {"escritura_id": escritura_id_str})

    return pago

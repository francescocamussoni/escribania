from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from events.publisher import publish
from models.escritura import Escritura, EstadoEscritura
from models.impuesto_escritura import ImpuestoEscritura
from models.pago_impuesto_escribania import PagoImpuestoEscribania
from schemas.impuesto import PagoImpuestoInput
from services.escritura_errors import EscrituraClosedError, EscrituraNotFoundError
from services.impuesto_service import ImpuestoNotFoundError

_CENTS = Decimal("0.01")


class PagoImpuestoEscribaniaNotFoundError(Exception):
    """Raised when updating or deleting a non-existent escribanía payment."""


def _ensure_open(escritura: Escritura) -> None:
    if escritura.estado == EstadoEscritura.CERRADA:
        raise EscrituraClosedError("Cannot modify a closed escritura")


async def _get_escritura_or_404(session: AsyncSession, escritura_id: uuid.UUID) -> Escritura:
    escritura = await session.get(Escritura, escritura_id)
    if escritura is None:
        raise EscrituraNotFoundError("Escritura not found")
    return escritura


async def _get_impuesto_or_404(
    session: AsyncSession,
    escritura_id: uuid.UUID,
    impuesto_id: uuid.UUID,
) -> ImpuestoEscritura:
    impuesto = await session.scalar(
        select(ImpuestoEscritura)
        .options(selectinload(ImpuestoEscritura.pago_escribania))
        .where(
            ImpuestoEscritura.id == impuesto_id,
            ImpuestoEscritura.escritura_id == escritura_id,
        )
    )
    if impuesto is None:
        raise ImpuestoNotFoundError("Impuesto not found")
    return impuesto


async def _get_pago_or_404(
    session: AsyncSession,
    escritura_id: uuid.UUID,
    impuesto_id: uuid.UUID,
) -> PagoImpuestoEscribania:
    impuesto = await _get_impuesto_or_404(session, escritura_id, impuesto_id)
    if impuesto.pago_escribania is None:
        raise PagoImpuestoEscribaniaNotFoundError("Escribanía payment not found for impuesto")
    return impuesto.pago_escribania


async def _publish_events(escritura_id: uuid.UUID, impuesto_id: uuid.UUID, pago_id: uuid.UUID) -> None:
    escritura_id_str = str(escritura_id)
    payload = {
        "escritura_id": escritura_id_str,
        "impuesto_id": str(impuesto_id),
        "pago_id": str(pago_id),
    }
    await publish("impuesto.pago_escribania.changed", payload)
    await publish("libros_updated", {"escritura_id": escritura_id_str})
    await publish("liquidacion.updated", {"escritura_id": escritura_id_str})


def _apply_payload(pago: PagoImpuestoEscribania, payload: PagoImpuestoInput) -> None:
    pago.monto = payload.monto.quantize(_CENTS)
    pago.fecha = payload.fecha


async def upsert_pago(
    session: AsyncSession,
    escritura_id: uuid.UUID,
    impuesto_id: uuid.UUID,
    payload: PagoImpuestoInput,
) -> PagoImpuestoEscribania:
    escritura = await _get_escritura_or_404(session, escritura_id)
    _ensure_open(escritura)
    impuesto = await _get_impuesto_or_404(session, escritura_id, impuesto_id)

    if impuesto.pago_escribania is None:
        pago = PagoImpuestoEscribania(
            id=uuid.uuid4(),
            impuesto_id=impuesto.id,
            escritura_id=escritura_id,
            monto=payload.monto.quantize(_CENTS),
            fecha=payload.fecha,
        )
        session.add(pago)
    else:
        pago = impuesto.pago_escribania
        _apply_payload(pago, payload)

    await session.commit()
    await session.refresh(pago)
    await _publish_events(escritura_id, impuesto_id, pago.id)
    return pago


async def update_pago(
    session: AsyncSession,
    escritura_id: uuid.UUID,
    impuesto_id: uuid.UUID,
    payload: PagoImpuestoInput,
) -> PagoImpuestoEscribania:
    escritura = await _get_escritura_or_404(session, escritura_id)
    _ensure_open(escritura)
    pago = await _get_pago_or_404(session, escritura_id, impuesto_id)
    _apply_payload(pago, payload)
    await session.commit()
    await session.refresh(pago)
    await _publish_events(escritura_id, impuesto_id, pago.id)
    return pago


async def delete_pago(
    session: AsyncSession,
    escritura_id: uuid.UUID,
    impuesto_id: uuid.UUID,
) -> None:
    escritura = await _get_escritura_or_404(session, escritura_id)
    _ensure_open(escritura)
    pago = await _get_pago_or_404(session, escritura_id, impuesto_id)
    await session.delete(pago)
    await session.commit()
    await _publish_events(escritura_id, impuesto_id, pago.id)

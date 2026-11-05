from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from events.publisher import publish
from models.escritura import Escritura, EstadoEscritura
from models.pago_colegio import PagoColegio, TipoPagoEscribania
from schemas.pago_colegio import PagoColegioResponse
from schemas.pago_colegio_bulk import (
    PagoColegioBulkMotivoNoElegible,
    PagoColegioBulkPreviewItem,
    PagoColegioBulkPreviewRequest,
    PagoColegioBulkPreviewResponse,
    PagoColegioBulkRequest,
    PagoColegioBulkResponse,
)
from services.escritura_errors import EscrituraNotFoundError
from services.escritura_service import compute_factura_efectiva
from services.plazo_colegio import sum_pagos_colegio

_ZERO = Decimal("0.00")
_TWOPLACES = Decimal("0.01")


class PagoColegioBulkValidationError(ValueError):
    """Raised when bulk confirm includes ineligible escrituras."""


def _quantize_money(value: Decimal) -> Decimal:
    return value.quantize(_TWOPLACES)


def compute_pendiente_colegio(escritura: Escritura) -> Decimal:
    if escritura.factura is None:
        raise RuntimeError("Escritura has no factura principal")
    efectiva = compute_factura_efectiva(escritura.factura)
    monto_pagado = sum_pagos_colegio(escritura.pagos_colegio)
    pendiente = _quantize_money(efectiva.total_impuestos_efectivo - monto_pagado)
    if pendiente < _ZERO:
        return _ZERO
    return pendiente


def _preview_item(escritura: Escritura) -> PagoColegioBulkPreviewItem:
    pendiente = compute_pendiente_colegio(escritura)
    motivo: PagoColegioBulkMotivoNoElegible | None = None
    elegible = True

    if escritura.estado == EstadoEscritura.CERRADA:
        elegible = False
        motivo = "cerrada"
    elif pendiente <= _ZERO:
        elegible = False
        motivo = "sin_pendiente"

    return PagoColegioBulkPreviewItem(
        escritura_id=escritura.id,
        escritura_nombre=escritura.nombre,
        pendiente=pendiente,
        elegible=elegible,
        motivo=motivo,
    )


def _is_eligible_for_bulk(escritura: Escritura) -> bool:
    if escritura.estado == EstadoEscritura.CERRADA:
        return False
    return compute_pendiente_colegio(escritura) > _ZERO


async def _load_escrituras(
    session: AsyncSession,
    escritura_ids: list[uuid.UUID],
) -> dict[uuid.UUID, Escritura]:
    if not escritura_ids:
        return {}

    stmt = (
        select(Escritura)
        .options(
            selectinload(Escritura.factura),
            selectinload(Escritura.pagos_colegio),
        )
        .where(Escritura.id.in_(escritura_ids))
    )
    escrituras = list((await session.execute(stmt)).scalars().all())
    found = {escritura.id: escritura for escritura in escrituras}
    missing = set(escritura_ids) - set(found.keys())
    if missing:
        missing_str = ", ".join(str(item) for item in sorted(missing))
        raise EscrituraNotFoundError(f"Escrituras not found: {missing_str}")
    return found


async def preview_bulk(
    session: AsyncSession,
    payload: PagoColegioBulkPreviewRequest,
) -> PagoColegioBulkPreviewResponse:
    escrituras = await _load_escrituras(session, payload.escritura_ids)
    items = [_preview_item(escrituras[escritura_id]) for escritura_id in payload.escritura_ids]
    total_propuesto = _quantize_money(
        sum((item.pendiente for item in items if item.elegible), _ZERO)
    )
    return PagoColegioBulkPreviewResponse(items=items, total_propuesto=total_propuesto)


async def confirm_bulk(
    session: AsyncSession,
    payload: PagoColegioBulkRequest,
) -> PagoColegioBulkResponse:
    escritura_ids = [item.escritura_id for item in payload.items]
    escrituras = await _load_escrituras(session, escritura_ids)

    ineligible_ids: list[uuid.UUID] = []
    for item in payload.items:
        if not _is_eligible_for_bulk(escrituras[item.escritura_id]):
            ineligible_ids.append(item.escritura_id)

    if ineligible_ids:
        ids_str = ", ".join(str(item) for item in sorted(ineligible_ids))
        raise PagoColegioBulkValidationError(
            f"Bulk confirm includes ineligible escrituras: {ids_str}"
        )

    pagos: list[PagoColegio] = []
    total = _ZERO
    for item in payload.items:
        pago = PagoColegio(
            id=uuid.uuid4(),
            escritura_id=item.escritura_id,
            monto=_quantize_money(item.monto),
            fecha=payload.fecha,
            concepto="",
            tipo=TipoPagoEscribania.COLEGIO,
        )
        session.add(pago)
        pagos.append(pago)
        total += pago.monto

    await session.commit()
    for pago in pagos:
        await session.refresh(pago)

    for pago in pagos:
        escritura_id_str = str(pago.escritura_id)
        await publish(
            "pago_colegio.created",
            {"escritura_id": escritura_id_str, "pago_id": str(pago.id)},
        )
        await publish("libros_updated", {"escritura_id": escritura_id_str})

    return PagoColegioBulkResponse(
        pagos=[PagoColegioResponse.model_validate(pago) for pago in pagos],
        total=_quantize_money(total),
    )

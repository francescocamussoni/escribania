from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from events.publisher import publish
from models.gasto_extraordinario import GastoExtraordinario
from schemas.gasto_extraordinario import (
    GastoExtraordinarioInput,
    GastoExtraordinarioResponse,
    GastosExtraordinariosListResponse,
    GastoExtraordinarioUpdate,
)
from services.liquidacion_service import month_bounds

_CENTS = Decimal("0.01")
_ZERO = Decimal("0.00")


class GastoExtraordinarioNotFoundError(Exception):
    """Raised when a gasto extraordinario does not exist."""


def _quantize_monto(value: Decimal) -> Decimal:
    return value.quantize(_CENTS)


async def _publish_event(
    event_type: str,
    gasto_id: uuid.UUID,
    fecha: date,
    *,
    extra_months: list[tuple[int, int]] | None = None,
) -> None:
    months = {(fecha.year, fecha.month)}
    if extra_months:
        months.update(extra_months)

    payload_base = {"gasto_extraordinario_id": str(gasto_id)}
    await publish(event_type, {**payload_base, "anio": fecha.year, "mes": fecha.month})

    for anio, mes in months:
        await publish("libros_updated", {"anio": anio, "mes": mes})


async def list_by_month(
    session: AsyncSession,
    anio: int,
    mes: int,
) -> GastosExtraordinariosListResponse:
    start, end = month_bounds(anio, mes)
    result = await session.scalars(
        select(GastoExtraordinario)
        .where(GastoExtraordinario.fecha >= start, GastoExtraordinario.fecha < end)
        .order_by(GastoExtraordinario.fecha, GastoExtraordinario.created_at)
    )
    gastos = list(result.all())
    total = sum((gasto.monto for gasto in gastos), _ZERO)
    return GastosExtraordinariosListResponse(
        anio=anio,
        mes=mes,
        gastos=[GastoExtraordinarioResponse.model_validate(gasto) for gasto in gastos],
        total=_quantize_monto(total),
    )


async def create_gasto(
    session: AsyncSession,
    payload: GastoExtraordinarioInput,
) -> GastoExtraordinarioResponse:
    gasto = GastoExtraordinario(
        id=uuid.uuid4(),
        concepto=payload.concepto,
        monto=_quantize_monto(payload.monto),
        fecha=payload.fecha,
    )
    session.add(gasto)
    await session.commit()
    await session.refresh(gasto)
    await _publish_event("gasto_extraordinario.created", gasto.id, gasto.fecha)
    return GastoExtraordinarioResponse.model_validate(gasto)


async def update_gasto(
    session: AsyncSession,
    gasto_id: uuid.UUID,
    payload: GastoExtraordinarioUpdate,
) -> GastoExtraordinarioResponse:
    gasto = await session.get(GastoExtraordinario, gasto_id)
    if gasto is None:
        raise GastoExtraordinarioNotFoundError("Gasto extraordinario not found")

    fecha_anterior = gasto.fecha
    if payload.concepto is not None:
        gasto.concepto = payload.concepto
    if payload.monto is not None:
        gasto.monto = _quantize_monto(payload.monto)
    if payload.fecha is not None:
        gasto.fecha = payload.fecha

    await session.commit()
    await session.refresh(gasto)

    extra_months: list[tuple[int, int]] | None = None
    if payload.fecha is not None and gasto.fecha != fecha_anterior:
        extra_months = [(fecha_anterior.year, fecha_anterior.month)]

    await _publish_event(
        "gasto_extraordinario.updated",
        gasto.id,
        gasto.fecha,
        extra_months=extra_months,
    )
    return GastoExtraordinarioResponse.model_validate(gasto)


async def delete_gasto(session: AsyncSession, gasto_id: uuid.UUID) -> None:
    gasto = await session.get(GastoExtraordinario, gasto_id)
    if gasto is None:
        raise GastoExtraordinarioNotFoundError("Gasto extraordinario not found")

    fecha = gasto.fecha
    await session.delete(gasto)
    await session.commit()
    await _publish_event("gasto_extraordinario.deleted", gasto_id, fecha)

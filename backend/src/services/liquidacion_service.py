from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.escritura import Escritura
from models.pago_cliente import PagoCliente
from schemas.liquidacion import (
    LiquidacionEscrituraItem,
    LiquidacionEscribano,
    LiquidacionResumen,
)
from services.escribano_service import list_active

_ZERO = Decimal("0.00")
_LEGACY_TOTAL_FIELDS = {
    "costanza": "total_costanza",
    "gabriel": "total_gabriel",
    "victoria": "total_victoria",
}


def month_bounds(anio: int, mes: int) -> tuple[date, date]:
    start = date(anio, mes, 1)
    if mes == 12:
        end = date(anio + 1, 1, 1)
    else:
        end = date(anio, mes + 1, 1)
    return start, end


def _legacy_total_key(nombre: str) -> str | None:
    return _LEGACY_TOTAL_FIELDS.get(nombre.strip().lower())


async def fetch_liquidacion_items_for_month(
    session: AsyncSession,
    anio: int,
    mes: int,
) -> list[LiquidacionEscrituraItem]:
    grouped, _, _ = await _group_items_by_escribano(session, anio, mes)
    items: list[LiquidacionEscrituraItem] = []
    for escribano_items in grouped.values():
        items.extend(escribano_items)
    return sorted(items, key=lambda item: item.nombre.lower())


async def _group_items_by_escribano(
    session: AsyncSession,
    anio: int,
    mes: int,
) -> tuple[dict[str, list[LiquidacionEscrituraItem]], dict[str, Decimal], dict[str, str]]:
    start, end = month_bounds(anio, mes)
    stmt = (
        select(PagoCliente)
        .join(Escritura)
        .options(selectinload(PagoCliente.escritura))
        .where(PagoCliente.fecha >= start, PagoCliente.fecha < end)
        .order_by(PagoCliente.fecha, PagoCliente.created_at)
    )
    pagos = list((await session.execute(stmt)).scalars().all())

    escritura_totals: dict[str, tuple[Escritura, Decimal]] = {}
    for pago in pagos:
        escritura = pago.escritura
        key = str(escritura.id)
        if key not in escritura_totals:
            escritura_totals[key] = (escritura, _ZERO)
        escritura, total = escritura_totals[key]
        escritura_totals[key] = (escritura, total + pago.monto)

    active_escribanos = await list_active(session)
    grouped: dict[str, list[LiquidacionEscrituraItem]] = {
        str(escribano.id): [] for escribano in active_escribanos
    }
    totals: dict[str, Decimal] = {str(escribano.id): _ZERO for escribano in active_escribanos}
    escribano_names: dict[str, str] = {
        str(escribano.id): escribano.nombre for escribano in active_escribanos
    }

    for escritura, monto in sorted(
        escritura_totals.values(),
        key=lambda pair: pair[0].nombre.lower(),
    ):
        item = LiquidacionEscrituraItem(
            escritura_id=str(escritura.id),
            nombre=escritura.nombre,
            estado=escritura.estado,
            monto_cobrado=monto.quantize(Decimal("0.01")),
        )
        key = str(escritura.escribano_id)
        if key not in grouped:
            grouped[key] = []
            totals[key] = _ZERO
            escribano_names[key] = escritura.escribano_nombre
        grouped[key].append(item)
        totals[key] += item.monto_cobrado

    return grouped, totals, escribano_names


async def get_liquidacion_mensual(
    session: AsyncSession,
    anio: int,
    mes: int,
) -> LiquidacionResumen:
    grouped, totals, escribano_names = await _group_items_by_escribano(session, anio, mes)

    por_escribano = [
        LiquidacionEscribano(
            escribano_id=escribano_id,
            escribano_nombre=escribano_names[escribano_id],
            total=totals[escribano_id],
            escrituras=grouped[escribano_id],
        )
        for escribano_id in sorted(
            grouped.keys(),
            key=lambda eid: escribano_names[eid].lower(),
        )
    ]

    legacy_totals = {field: _ZERO for field in _LEGACY_TOTAL_FIELDS.values()}
    for escribano_id, total in totals.items():
        legacy_key = _legacy_total_key(escribano_names[escribano_id])
        if legacy_key is not None:
            legacy_totals[legacy_key] += total

    total_global = sum(totals.values(), _ZERO)

    return LiquidacionResumen(
        anio=anio,
        mes=mes,
        total_costanza=legacy_totals["total_costanza"],
        total_gabriel=legacy_totals["total_gabriel"],
        total_victoria=legacy_totals["total_victoria"],
        total_global=total_global,
        por_escribano=por_escribano,
    )


async def close_liquidacion_mensual(
    session: AsyncSession,
    anio: int,
    mes: int,
) -> None:
    """Month-close hook: snapshots employee salaries for the closed period."""
    from services.empleado_service import snapshot_month  # noqa: PLC0415

    await snapshot_month(session, anio, mes)

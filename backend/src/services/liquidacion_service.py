from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.escritura import Escritura, Escribano
from models.factura_principal import FacturaPrincipal
from schemas.liquidacion import (
    LiquidacionEscrituraItem,
    LiquidacionEscribano,
    LiquidacionResumen,
)

ALL_ESCRIBANOS = (Escribano.COSTANZA, Escribano.GABRIEL, Escribano.VICTORIA)
ZERO = Decimal("0.00")


def month_bounds(anio: int, mes: int) -> tuple[datetime, datetime]:
    start = datetime(anio, mes, 1, tzinfo=UTC)
    if mes == 12:
        end = datetime(anio + 1, 1, 1, tzinfo=UTC)
    else:
        end = datetime(anio, mes + 1, 1, tzinfo=UTC)
    return start, end


def _subtotal(factura: FacturaPrincipal) -> Decimal:
    return factura.honorario_principal + factura.certificacion


def _to_item(escritura: Escritura, factura: FacturaPrincipal) -> LiquidacionEscrituraItem:
    subtotal = _subtotal(factura)
    return LiquidacionEscrituraItem(
        escritura_id=str(escritura.id),
        nombre=escritura.nombre,
        estado=escritura.estado,
        honorario_principal=factura.honorario_principal,
        certificacion=factura.certificacion,
        subtotal=subtotal,
    )


async def fetch_escrituras_for_month(
    session: AsyncSession,
    anio: int,
    mes: int,
) -> list[tuple[Escritura, FacturaPrincipal]]:
    start, end = month_bounds(anio, mes)
    stmt = (
        select(Escritura, FacturaPrincipal)
        .join(FacturaPrincipal, FacturaPrincipal.escritura_id == Escritura.id)
        .options(selectinload(Escritura.factura))
        .where(Escritura.created_at >= start, Escritura.created_at < end)
        .order_by(Escritura.created_at)
    )
    rows = (await session.execute(stmt)).all()
    return [(row[0], row[1]) for row in rows]


async def get_liquidacion_mensual(
    session: AsyncSession,
    anio: int,
    mes: int,
) -> LiquidacionResumen:
    rows = await fetch_escrituras_for_month(session, anio, mes)

    grouped: dict[Escribano, list[LiquidacionEscrituraItem]] = {e: [] for e in ALL_ESCRIBANOS}
    totals: dict[Escribano, Decimal] = {e: ZERO for e in ALL_ESCRIBANOS}

    for escritura, factura in rows:
        item = _to_item(escritura, factura)
        grouped[escritura.escribano].append(item)
        totals[escritura.escribano] += item.subtotal

    por_escribano = [
        LiquidacionEscribano(
            escribano=escribano,
            total=totals[escribano],
            escrituras=grouped[escribano],
        )
        for escribano in ALL_ESCRIBANOS
    ]

    total_global = sum(totals.values(), ZERO)

    return LiquidacionResumen(
        anio=anio,
        mes=mes,
        total_costanza=totals[Escribano.COSTANZA],
        total_gabriel=totals[Escribano.GABRIEL],
        total_victoria=totals[Escribano.VICTORIA],
        total_global=total_global,
        por_escribano=por_escribano,
    )

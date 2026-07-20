from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.escritura import Escritura
from models.factura_principal import FacturaPrincipal
from schemas.liquidacion import (
    LiquidacionEscrituraItem,
    LiquidacionEscribano,
    LiquidacionResumen,
)
from services.escribano_service import list_active

ZERO = Decimal("0.00")
_LEGACY_TOTAL_FIELDS = {
    "costanza": "total_costanza",
    "gabriel": "total_gabriel",
    "victoria": "total_victoria",
}


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


def _legacy_total_key(nombre: str) -> str | None:
    return _LEGACY_TOTAL_FIELDS.get(nombre.strip().lower())


async def get_liquidacion_mensual(
    session: AsyncSession,
    anio: int,
    mes: int,
) -> LiquidacionResumen:
    rows = await fetch_escrituras_for_month(session, anio, mes)
    active_escribanos = await list_active(session)

    grouped: dict[str, list[LiquidacionEscrituraItem]] = {
        str(escribano.id): [] for escribano in active_escribanos
    }
    totals: dict[str, Decimal] = {str(escribano.id): ZERO for escribano in active_escribanos}
    escribano_names: dict[str, str] = {
        str(escribano.id): escribano.nombre for escribano in active_escribanos
    }

    for escritura, factura in rows:
        key = str(escritura.escribano_id)
        item = _to_item(escritura, factura)
        if key not in grouped:
            grouped[key] = []
            totals[key] = ZERO
            escribano_names[key] = escritura.escribano_nombre
        grouped[key].append(item)
        totals[key] += item.subtotal

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

    legacy_totals = {field: ZERO for field in _LEGACY_TOTAL_FIELDS.values()}
    for escribano_id, total in totals.items():
        legacy_key = _legacy_total_key(escribano_names[escribano_id])
        if legacy_key is not None:
            legacy_totals[legacy_key] += total

    total_global = sum(totals.values(), ZERO)

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

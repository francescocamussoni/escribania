from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.escritura import Escritura
from models.pago_cliente import PagoCliente
from models.pago_impuesto_cliente import PagoImpuestoCliente
from models.pago_impuesto_escribania import PagoImpuestoEscribania
from schemas.liquidacion import (
    LiquidacionEscrituraItem,
    LiquidacionEscribano,
    LiquidacionResumen,
)
from services.escribano_service import list_active

_ZERO = Decimal("0.00")
_QUANT = Decimal("0.01")
_LEGACY_TOTAL_FIELDS = {
    "costanza": "total_costanza",
    "gabriel": "total_gabriel",
    "monica": "total_monica",
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


def _money(value: Decimal) -> Decimal:
    return value.quantize(_QUANT)


class _EscrituraMonthTotals:
    __slots__ = ("escritura", "monto_cobrado", "neto_cliente", "neto_escribania")

    def __init__(self, escritura: Escritura) -> None:
        self.escritura = escritura
        self.monto_cobrado = _ZERO
        self.neto_cliente = _ZERO
        self.neto_escribania = _ZERO

    def has_activity(self) -> bool:
        return (
            self.monto_cobrado != _ZERO
            or self.neto_cliente != _ZERO
            or self.neto_escribania != _ZERO
        )

    @property
    def neto_impuestos(self) -> Decimal:
        return _money(self.neto_cliente - self.neto_escribania)

    @property
    def total_liquidacion(self) -> Decimal:
        return _money(self.monto_cobrado + self.neto_impuestos)


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
    pagos_cliente_stmt = (
        select(PagoCliente)
        .join(Escritura)
        .options(selectinload(PagoCliente.escritura))
        .where(PagoCliente.fecha >= start, PagoCliente.fecha < end)
        .order_by(PagoCliente.fecha, PagoCliente.created_at)
    )
    pagos_impuesto_cliente_stmt = (
        select(PagoImpuestoCliente)
        .join(Escritura)
        .options(selectinload(PagoImpuestoCliente.escritura))
        .where(PagoImpuestoCliente.fecha >= start, PagoImpuestoCliente.fecha < end)
    )
    pagos_impuesto_escribania_stmt = (
        select(PagoImpuestoEscribania)
        .join(Escritura)
        .options(selectinload(PagoImpuestoEscribania.escritura))
        .where(PagoImpuestoEscribania.fecha >= start, PagoImpuestoEscribania.fecha < end)
    )
    pagos_cliente = list((await session.execute(pagos_cliente_stmt)).scalars().all())
    pagos_impuesto_cliente = list(
        (await session.execute(pagos_impuesto_cliente_stmt)).scalars().all()
    )
    pagos_impuesto_escribania = list(
        (await session.execute(pagos_impuesto_escribania_stmt)).scalars().all()
    )

    escritura_totals: dict[str, _EscrituraMonthTotals] = {}

    def _ensure(escritura: Escritura) -> _EscrituraMonthTotals:
        key = str(escritura.id)
        if key not in escritura_totals:
            escritura_totals[key] = _EscrituraMonthTotals(escritura)
        return escritura_totals[key]

    for pago in pagos_cliente:
        row = _ensure(pago.escritura)
        row.monto_cobrado += pago.monto

    for pago in pagos_impuesto_cliente:
        row = _ensure(pago.escritura)
        row.neto_cliente += pago.monto

    for pago in pagos_impuesto_escribania:
        row = _ensure(pago.escritura)
        row.neto_escribania += pago.monto

    active_escribanos = await list_active(session)
    grouped: dict[str, list[LiquidacionEscrituraItem]] = {
        str(escribano.id): [] for escribano in active_escribanos
    }
    totals: dict[str, Decimal] = {str(escribano.id): _ZERO for escribano in active_escribanos}
    escribano_names: dict[str, str] = {
        str(escribano.id): escribano.nombre for escribano in active_escribanos
    }

    for row in sorted(
        escritura_totals.values(),
        key=lambda item: item.escritura.nombre.lower(),
    ):
        if not row.has_activity():
            continue
        item = LiquidacionEscrituraItem(
            escritura_id=str(row.escritura.id),
            nombre=row.escritura.nombre,
            estado=row.escritura.estado,
            monto_cobrado=_money(row.monto_cobrado),
            neto_impuestos=row.neto_impuestos,
        )
        key = str(row.escritura.escribano_id)
        if key not in grouped:
            grouped[key] = []
            totals[key] = _ZERO
            escribano_names[key] = row.escritura.escribano_nombre
        grouped[key].append(item)
        totals[key] += row.total_liquidacion

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
        total_monica=legacy_totals["total_monica"],
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

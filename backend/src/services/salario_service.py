from __future__ import annotations

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from schemas.salarios import PagoEscribano, PagoSalariosResumen, PagoSecretaria
from services.empleado_service import list_active as list_active_empleados
from services.escribano_service import list_active as list_active_escribanos
from services.gasto_extraordinario_reparto import reparto_equitativo
from services.gasto_extraordinario_service import list_by_month
from services.liquidacion_service import _group_items_by_escribano

_ZERO = Decimal("0.00")
_CENTS = Decimal("0.01")

_ADVERTENCIA_SIN_ESCRIBANOS = (
    "No hay escribanos activos; los gastos extraordinarios del mes no pueden repartirse."
)


def _money(value: Decimal) -> Decimal:
    return value.quantize(_CENTS)


async def _deducciones_por_escribano(
    session: AsyncSession,
    anio: int,
    mes: int,
) -> tuple[Decimal, dict[str, Decimal], str | None]:
    gastos = await list_by_month(session, anio, mes)
    total_gastos = gastos.total

    active_escribanos = await list_active_escribanos(session)
    sorted_escribanos = sorted(active_escribanos, key=lambda escribano: escribano.nombre.lower())
    cantidad = len(sorted_escribanos)

    advertencia: str | None = None
    if cantidad == 0 and total_gastos > _ZERO:
        advertencia = _ADVERTENCIA_SIN_ESCRIBANOS

    cuotas = reparto_equitativo(total_gastos, cantidad)
    deducciones = {
        str(escribano.id): _money(cuota)
        for escribano, cuota in zip(sorted_escribanos, cuotas, strict=True)
    }
    return _money(total_gastos), deducciones, advertencia


async def get_pagos_mensuales(
    session: AsyncSession,
    anio: int,
    mes: int,
) -> PagoSalariosResumen:
    grouped, totals, names = await _group_items_by_escribano(session, anio, mes)
    total_gastos, deducciones, advertencia = await _deducciones_por_escribano(session, anio, mes)
    active_empleados = await list_active_empleados(session)

    escribanos = [
        PagoEscribano(
            nombre=names[escribano_id],
            monto_total=totals[escribano_id],
            deduccion_gastos_extraordinarios=deducciones.get(escribano_id, _ZERO),
            monto_neto=_money(totals[escribano_id] - deducciones.get(escribano_id, _ZERO)),
            escrituras=grouped[escribano_id],
        )
        for escribano_id in sorted(names.keys(), key=lambda eid: names[eid].lower())
    ]

    base_total = sum((empleado.sueldo for empleado in active_empleados), _ZERO)
    secretarias = [
        PagoSecretaria(nombre=empleado.nombre, monto=empleado.sueldo, base_total=base_total)
        for empleado in sorted(active_empleados, key=lambda e: e.nombre.lower())
    ]

    return PagoSalariosResumen(
        anio=anio,
        mes=mes,
        escribanos=escribanos,
        secretarias=secretarias,
        total_gastos_extraordinarios=total_gastos,
        advertencia_reparto=advertencia,
    )

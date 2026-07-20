from __future__ import annotations

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from schemas.liquidacion import LiquidacionEscrituraItem
from schemas.salarios import PagoEscribano, PagoSalariosResumen, PagoSecretaria
from services.empleado_service import list_active as list_active_empleados
from services.escribano_service import list_active as list_active_escribanos
from services.liquidacion_service import _to_item, fetch_escrituras_for_month

ZERO = Decimal("0.00")


async def get_pagos_mensuales(
    session: AsyncSession,
    anio: int,
    mes: int,
) -> PagoSalariosResumen:
    rows = await fetch_escrituras_for_month(session, anio, mes)
    active_escribanos = await list_active_escribanos(session)
    active_empleados = await list_active_empleados(session)

    grouped: dict[str, list[LiquidacionEscrituraItem]] = {
        str(escribano.id): [] for escribano in active_escribanos
    }
    totals: dict[str, Decimal] = {str(escribano.id): ZERO for escribano in active_escribanos}
    names: dict[str, str] = {str(escribano.id): escribano.nombre for escribano in active_escribanos}

    for escritura, factura in rows:
        key = str(escritura.escribano_id)
        item = _to_item(escritura, factura)
        if key not in grouped:
            grouped[key] = []
            totals[key] = ZERO
            names[key] = escritura.escribano_nombre
        grouped[key].append(item)
        totals[key] += item.subtotal

    escribanos = [
        PagoEscribano(
            nombre=names[escribano_id],
            monto_total=totals[escribano_id],
            escrituras=grouped[escribano_id],
        )
        for escribano_id in sorted(names.keys(), key=lambda eid: names[eid].lower())
    ]

    base_total = sum((empleado.sueldo for empleado in active_empleados), ZERO)
    secretarias = [
        PagoSecretaria(nombre=empleado.nombre, monto=empleado.sueldo, base_total=base_total)
        for empleado in sorted(active_empleados, key=lambda e: e.nombre.lower())
    ]

    return PagoSalariosResumen(
        anio=anio,
        mes=mes,
        escribanos=escribanos,
        secretarias=secretarias,
    )

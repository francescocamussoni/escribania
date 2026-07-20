from __future__ import annotations

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from schemas.salarios import PagoEscribano, PagoSalariosResumen, PagoSecretaria
from services.empleado_service import list_active as list_active_empleados
from services.liquidacion_service import _group_items_by_escribano

_ZERO = Decimal("0.00")


async def get_pagos_mensuales(
    session: AsyncSession,
    anio: int,
    mes: int,
) -> PagoSalariosResumen:
    grouped, totals, names = await _group_items_by_escribano(session, anio, mes)
    active_empleados = await list_active_empleados(session)

    escribanos = [
        PagoEscribano(
            nombre=names[escribano_id],
            monto_total=totals[escribano_id],
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
    )

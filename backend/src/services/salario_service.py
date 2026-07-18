from __future__ import annotations

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from models.escritura import Escribano
from schemas.liquidacion import LiquidacionEscrituraItem
from schemas.salarios import PagoEscribano, PagoSalariosResumen, PagoSecretaria
from services.escritura_service import get_active_config
from services.liquidacion_service import ALL_ESCRIBANOS, _to_item, fetch_escrituras_for_month

ESCRIBANO_LABELS: dict[Escribano, str] = {
    Escribano.COSTANZA: "Costanza",
    Escribano.GABRIEL: "Gabriel",
    Escribano.VICTORIA: "Victoria",
}
SECRETARIAS = ("Graciela", "Guadalupe")
ZERO = Decimal("0.00")


async def get_pagos_mensuales(
    session: AsyncSession,
    anio: int,
    mes: int,
) -> PagoSalariosResumen:
    rows = await fetch_escrituras_for_month(session, anio, mes)
    config = await get_active_config(session)

    grouped: dict[Escribano, list[LiquidacionEscrituraItem]] = {e: [] for e in ALL_ESCRIBANOS}
    totals: dict[Escribano, Decimal] = {e: ZERO for e in ALL_ESCRIBANOS}

    for escritura, factura in rows:
        item = _to_item(escritura, factura)
        grouped[escritura.escribano].append(item)
        totals[escritura.escribano] += item.subtotal

    escribanos = [
        PagoEscribano(
            nombre=ESCRIBANO_LABELS[escribano],
            monto_total=totals[escribano],
            escrituras=grouped[escribano],
        )
        for escribano in ALL_ESCRIBANOS
    ]

    base_total = config.salario_secretarias_total
    monto_secretaria = base_total / Decimal("2")
    secretarias = [
        PagoSecretaria(nombre=nombre, monto=monto_secretaria, base_total=base_total)
        for nombre in SECRETARIAS
    ]

    return PagoSalariosResumen(
        anio=anio,
        mes=mes,
        escribanos=escribanos,
        secretarias=secretarias,
    )

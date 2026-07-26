"""Remove local dev data that is not part of the [DEMO] seed.

Deletes escrituras whose nombre does not start with '[DEMO]' and related rows,
plus gastos extraordinarios without the [DEMO] prefix.

Safe to run only when ENVIRONMENT=local. Does not touch escribanos, empleados, or config.
"""

from __future__ import annotations

import asyncio

from sqlalchemy import delete, select

from config import get_settings
from database import AsyncSessionLocal
from models.escritura import Escritura
from models.factura_principal import FacturaPrincipal
from models.gasto_extraordinario import GastoExtraordinario
from models.impuesto_escritura import ImpuestoEscritura
from models.pago_cliente import PagoCliente
from models.pago_colegio import PagoColegio
from models.pago_impuesto_cliente import PagoImpuestoCliente
from models.pago_impuesto_escribania import PagoImpuestoEscribania

DEMO_PREFIX = "[DEMO]"

_NON_DEMO_ESCRITURA = ~Escritura.nombre.like(f"{DEMO_PREFIX}%")
_NON_DEMO_GASTO = ~GastoExtraordinario.concepto.like(f"{DEMO_PREFIX}%")


async def cleanup_non_demo() -> None:
    settings = get_settings()
    if settings.environment != "local":
        print("cleanup_non_demo_data skipped — ENVIRONMENT is not 'local'.")
        return

    async with AsyncSessionLocal() as session:
        ids = list(await session.scalars(select(Escritura.id).where(_NON_DEMO_ESCRITURA)))
        if ids:
            await session.execute(delete(PagoCliente).where(PagoCliente.escritura_id.in_(ids)))
            await session.execute(delete(PagoColegio).where(PagoColegio.escritura_id.in_(ids)))
            await session.execute(
                delete(PagoImpuestoCliente).where(PagoImpuestoCliente.escritura_id.in_(ids))
            )
            await session.execute(
                delete(PagoImpuestoEscribania).where(PagoImpuestoEscribania.escritura_id.in_(ids))
            )
            await session.execute(
                delete(ImpuestoEscritura).where(ImpuestoEscritura.escritura_id.in_(ids))
            )
            await session.execute(delete(FacturaPrincipal).where(FacturaPrincipal.escritura_id.in_(ids)))
            await session.execute(delete(Escritura).where(Escritura.id.in_(ids)))
            print(f"Removed {len(ids)} non-demo escrituras.")

        gastos = await session.execute(delete(GastoExtraordinario).where(_NON_DEMO_GASTO))
        gasto_count = gastos.rowcount or 0
        if gasto_count:
            print(f"Removed {gasto_count} non-demo gastos extraordinarios.")

        if not ids and not gasto_count:
            print("No non-demo data to remove.")
        else:
            await session.commit()


if __name__ == "__main__":
    asyncio.run(cleanup_non_demo())

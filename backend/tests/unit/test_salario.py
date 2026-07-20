from datetime import UTC, date, datetime
from decimal import Decimal
import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from models.empleado import Empleado
from models.escritura import EstadoEscritura
from models.pago_cliente import PagoCliente
from services.salario_service import get_pagos_mensuales
from helpers.escritura_factory import insert_test_escritura

TEST_YEAR = 2026
TEST_MONTH = 7

pytestmark = pytest.mark.usefixtures("isolated_liquidacion_month")


def _dt(day: int) -> datetime:
    return datetime(TEST_YEAR, TEST_MONTH, day, 12, 0, 0, tzinfo=UTC)


def _payment_date(day: int = 15) -> date:
    return date(TEST_YEAR, TEST_MONTH, day)


async def _insert_pago_cliente(
    session: AsyncSession,
    escritura_id: uuid.UUID,
    *,
    monto: Decimal,
    fecha: date,
) -> PagoCliente:
    pago = PagoCliente(
        id=uuid.uuid4(),
        escritura_id=escritura_id,
        concepto="Pago test",
        monto=monto,
        fecha=fecha,
    )
    session.add(pago)
    await session.commit()
    return pago


@pytest.mark.asyncio
async def test_escribano_payment_sums_monto_cobrado(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session,
            seeded_config,
            escribano_nombre="Costanza",
            created_at=_dt(10),
        )
        cleanup_escrituras.append(escritura.id)
        await _insert_pago_cliente(
            session,
            escritura.id,
            monto=Decimal("250000.00"),
            fecha=_payment_date(),
        )

        pagos = await get_pagos_mensuales(session, TEST_YEAR, TEST_MONTH)

    costanza = next(p for p in pagos.escribanos if p.nombre == "Costanza")
    assert costanza.monto_total == Decimal("250000.00")
    assert len(costanza.escrituras) == 1
    assert costanza.escrituras[0].escritura_id == str(escritura.id)
    assert costanza.escrituras[0].monto_cobrado == Decimal("250000.00")


@pytest.mark.asyncio
async def test_secretaria_payment_uses_active_empleados(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
) -> None:
    async with session_factory() as session:
        empleados = list((await session.execute(select(Empleado))).scalars().all())
        pagos = await get_pagos_mensuales(session, TEST_YEAR, TEST_MONTH)

    expected_total = sum((empleado.sueldo for empleado in empleados), Decimal("0.00"))
    assert len(pagos.secretarias) == len(empleados)
    for secretaria in pagos.secretarias:
        empleado = next(e for e in empleados if e.nombre == secretaria.nombre)
        assert secretaria.base_total == expected_total
        assert secretaria.monto == empleado.sueldo


@pytest.mark.asyncio
async def test_pago_escribano_detail_contains_escritura_id_and_monto_cobrado(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session,
            seeded_config,
            escribano_nombre="Gabriel",
            created_at=_dt(15),
            estado=EstadoEscritura.CERRADA,
        )
        cleanup_escrituras.append(escritura.id)
        await _insert_pago_cliente(
            session,
            escritura.id,
            monto=Decimal("180000.00"),
            fecha=_payment_date(),
        )

        pagos = await get_pagos_mensuales(session, TEST_YEAR, TEST_MONTH)

    gabriel = next(p for p in pagos.escribanos if p.nombre == "Gabriel")
    assert gabriel.escrituras[0].escritura_id == str(escritura.id)
    assert gabriel.escrituras[0].estado == EstadoEscritura.CERRADA
    assert gabriel.escrituras[0].monto_cobrado == Decimal("180000.00")

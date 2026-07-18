from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from models.escritura import Escribano, EstadoEscritura
from services.escritura_service import get_active_config
from services.salario_service import SECRETARIAS, get_pagos_mensuales
from helpers.escritura_factory import CANONICAL_SUBTOTAL, insert_test_escritura

TEST_YEAR = 2026
TEST_MONTH = 7

pytestmark = pytest.mark.usefixtures("isolated_liquidacion_month")


def _dt(day: int) -> datetime:
    return datetime(TEST_YEAR, TEST_MONTH, day, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def session_factory(db_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.mark.asyncio
async def test_escribano_payment_sums_honorario_and_certificacion(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session,
            seeded_config,
            escribano=Escribano.COSTANZA,
            created_at=_dt(10),
        )
        cleanup_escrituras.append(escritura.id)

        pagos = await get_pagos_mensuales(session, TEST_YEAR, TEST_MONTH)

    costanza = next(p for p in pagos.escribanos if p.nombre == "Costanza")
    assert costanza.monto_total == CANONICAL_SUBTOTAL
    assert len(costanza.escrituras) == 1
    assert costanza.escrituras[0].escritura_id == str(escritura.id)


@pytest.mark.asyncio
async def test_secretaria_payment_is_half_of_config_total(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
) -> None:
    async with session_factory() as session:
        config = await get_active_config(session)
        pagos = await get_pagos_mensuales(session, TEST_YEAR, TEST_MONTH)

    expected_half = config.salario_secretarias_total / Decimal("2")
    assert len(pagos.secretarias) == 2
    for secretaria in pagos.secretarias:
        assert secretaria.nombre in SECRETARIAS
        assert secretaria.base_total == config.salario_secretarias_total
        assert secretaria.monto == expected_half


@pytest.mark.asyncio
async def test_pago_escribano_detail_contains_escritura_id(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session,
            seeded_config,
            escribano=Escribano.GABRIEL,
            created_at=_dt(15),
            estado=EstadoEscritura.CERRADA,
        )
        cleanup_escrituras.append(escritura.id)

        pagos = await get_pagos_mensuales(session, TEST_YEAR, TEST_MONTH)

    gabriel = next(p for p in pagos.escribanos if p.nombre == "Gabriel")
    assert gabriel.escrituras[0].escritura_id == str(escritura.id)
    assert gabriel.escrituras[0].estado == EstadoEscritura.CERRADA

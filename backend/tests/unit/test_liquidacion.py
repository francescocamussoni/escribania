from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from models.escritura import EstadoEscritura
from services.liquidacion_service import get_liquidacion_mensual
from helpers.escritura_factory import (
    CANONICAL_SUBTOTAL,
    insert_test_escritura,
)

TEST_YEAR = 2026
TEST_MONTH = 7

pytestmark = pytest.mark.usefixtures("isolated_liquidacion_month")


def _dt(day: int) -> datetime:
    return datetime(TEST_YEAR, TEST_MONTH, day, 12, 0, 0, tzinfo=UTC)


def _prev_month_dt(day: int) -> datetime:
    return datetime(TEST_YEAR, TEST_MONTH - 1, day, 12, 0, 0, tzinfo=UTC)


@pytest.mark.asyncio
async def test_open_escritura_in_month_is_included(
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
            estado=EstadoEscritura.ABIERTA,
        )
        cleanup_escrituras.append(escritura.id)

        resumen = await get_liquidacion_mensual(session, TEST_YEAR, TEST_MONTH)

    costanza = next(e for e in resumen.por_escribano if e.escribano_nombre == "Costanza")
    assert len(costanza.escrituras) == 1
    assert costanza.escrituras[0].escritura_id == str(escritura.id)


@pytest.mark.asyncio
async def test_closed_same_month_escritura_is_included(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session,
            seeded_config,
            escribano_nombre="Gabriel",
            created_at=_dt(12),
            estado=EstadoEscritura.CERRADA,
        )
        cleanup_escrituras.append(escritura.id)

        resumen = await get_liquidacion_mensual(session, TEST_YEAR, TEST_MONTH)

    gabriel = next(e for e in resumen.por_escribano if e.escribano_nombre == "Gabriel")
    assert len(gabriel.escrituras) == 1
    assert gabriel.escrituras[0].estado == EstadoEscritura.CERRADA


@pytest.mark.asyncio
async def test_previous_month_escritura_excluded(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session,
            seeded_config,
            escribano_nombre="Victoria",
            created_at=_prev_month_dt(20),
            estado=EstadoEscritura.CERRADA,
        )
        cleanup_escrituras.append(escritura.id)

        resumen = await get_liquidacion_mensual(session, TEST_YEAR, TEST_MONTH)

    victoria = next(e for e in resumen.por_escribano if e.escribano_nombre == "Victoria")
    assert victoria.escrituras == []
    assert victoria.total == Decimal("0.00")


@pytest.mark.asyncio
async def test_per_escribano_totals_sum_honorario_plus_certificacion(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    async with session_factory() as session:
        e1 = await insert_test_escritura(
            session,
            seeded_config,
            escribano_nombre="Costanza",
            created_at=_dt(5),
            nombre="Costanza 1",
        )
        e2 = await insert_test_escritura(
            session,
            seeded_config,
            escribano_nombre="Costanza",
            created_at=_dt(8),
            nombre="Costanza 2",
        )
        cleanup_escrituras.extend([e1.id, e2.id])

        resumen = await get_liquidacion_mensual(session, TEST_YEAR, TEST_MONTH)

    costanza = next(e for e in resumen.por_escribano if e.escribano_nombre == "Costanza")
    assert costanza.total == CANONICAL_SUBTOTAL * 2
    assert resumen.total_costanza == CANONICAL_SUBTOTAL * 2
    assert resumen.total_global == CANONICAL_SUBTOTAL * 2

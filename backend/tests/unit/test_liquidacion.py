from datetime import UTC, date, datetime
from decimal import Decimal
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from models.escritura import EstadoEscritura
from models.pago_cliente import PagoCliente
from services.liquidacion_service import get_liquidacion_mensual
from helpers.escritura_factory import insert_test_escritura

TEST_YEAR = 2026
TEST_MONTH = 7
PAYMENT_DAY = 15

pytestmark = pytest.mark.usefixtures("isolated_liquidacion_month")


def _dt(day: int) -> datetime:
    return datetime(TEST_YEAR, TEST_MONTH, day, 12, 0, 0, tzinfo=UTC)


def _payment_date(day: int = PAYMENT_DAY) -> date:
    return date(TEST_YEAR, TEST_MONTH, day)


def _prev_month_payment_date(day: int = 20) -> date:
    return date(TEST_YEAR, TEST_MONTH - 1, day)


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
async def test_escritura_with_partial_payment_in_month_is_included(
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
        await _insert_pago_cliente(
            session,
            escritura.id,
            monto=Decimal("400000.00"),
            fecha=_payment_date(),
        )

        resumen = await get_liquidacion_mensual(session, TEST_YEAR, TEST_MONTH)

    costanza = next(e for e in resumen.por_escribano if e.escribano_nombre == "Costanza")
    assert len(costanza.escrituras) == 1
    assert costanza.escrituras[0].escritura_id == str(escritura.id)
    assert costanza.escrituras[0].monto_cobrado == Decimal("400000.00")


@pytest.mark.asyncio
async def test_escritura_without_payments_in_month_is_excluded(
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
            estado=EstadoEscritura.ABIERTA,
        )
        cleanup_escrituras.append(escritura.id)

        resumen = await get_liquidacion_mensual(session, TEST_YEAR, TEST_MONTH)

    gabriel = next(e for e in resumen.por_escribano if e.escribano_nombre == "Gabriel")
    assert gabriel.escrituras == []
    assert gabriel.total == Decimal("0.00")


@pytest.mark.asyncio
async def test_two_payments_in_month_produce_single_summed_line(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session,
            seeded_config,
            escribano_nombre="Costanza",
            created_at=_dt(5),
            nombre="Pagos múltiples",
        )
        cleanup_escrituras.append(escritura.id)
        await _insert_pago_cliente(
            session,
            escritura.id,
            monto=Decimal("100000.00"),
            fecha=_payment_date(10),
        )
        await _insert_pago_cliente(
            session,
            escritura.id,
            monto=Decimal("50000.00"),
            fecha=_payment_date(20),
        )

        resumen = await get_liquidacion_mensual(session, TEST_YEAR, TEST_MONTH)

    costanza = next(e for e in resumen.por_escribano if e.escribano_nombre == "Costanza")
    assert len(costanza.escrituras) == 1
    assert costanza.escrituras[0].monto_cobrado == Decimal("150000.00")


@pytest.mark.asyncio
async def test_previous_month_payment_does_not_count(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session,
            seeded_config,
            escribano_nombre="Victoria",
            created_at=_dt(8),
            estado=EstadoEscritura.CERRADA,
        )
        cleanup_escrituras.append(escritura.id)
        await _insert_pago_cliente(
            session,
            escritura.id,
            monto=Decimal("999999.00"),
            fecha=_prev_month_payment_date(),
        )

        resumen = await get_liquidacion_mensual(session, TEST_YEAR, TEST_MONTH)

    victoria = next(e for e in resumen.por_escribano if e.escribano_nombre == "Victoria")
    assert victoria.escrituras == []
    assert victoria.total == Decimal("0.00")


@pytest.mark.asyncio
async def test_per_escribano_totals_sum_monto_cobrado(
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
        await _insert_pago_cliente(
            session,
            e1.id,
            monto=Decimal("200000.00"),
            fecha=_payment_date(),
        )
        await _insert_pago_cliente(
            session,
            e2.id,
            monto=Decimal("300000.00"),
            fecha=_payment_date(18),
        )

        resumen = await get_liquidacion_mensual(session, TEST_YEAR, TEST_MONTH)

    costanza = next(e for e in resumen.por_escribano if e.escribano_nombre == "Costanza")
    assert costanza.total == Decimal("500000.00")
    assert resumen.total_costanza == Decimal("500000.00")
    assert resumen.total_global == Decimal("500000.00")

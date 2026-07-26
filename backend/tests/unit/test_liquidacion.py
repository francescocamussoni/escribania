from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from models.escritura import EstadoEscritura
from models.impuesto_escritura import DireccionProrrateo, TipoImpuesto
from models.pago_cliente import PagoCliente
from schemas.impuesto import ImpuestoInput, PagoImpuestoInput
from services.impuesto_service import create_impuesto
from services.liquidacion_service import close_liquidacion_mensual, get_liquidacion_mensual
from helpers.escritura_factory import insert_test_escritura

TEST_YEAR = 2030
TEST_MONTH = 7
PAYMENT_DAY = 15

pytestmark = pytest.mark.usefixtures("isolated_liquidacion_month")


def _dt(day: int) -> datetime:
    return datetime(TEST_YEAR, TEST_MONTH, day, 12, 0, 0, tzinfo=UTC)


def _payment_date(day: int = PAYMENT_DAY) -> date:
    return date(TEST_YEAR, TEST_MONTH, day)


def _prev_month_payment_date(day: int = 20) -> date:
    return date(TEST_YEAR, TEST_MONTH - 1, day)


def _impuesto_input() -> ImpuestoInput:
    return ImpuestoInput(
        tipo=TipoImpuesto.API,
        monto_total=Decimal("10000.00"),
        periodo_inicio=date(2026, 5, 1),
        periodo_fin=date(2026, 6, 30),
        fecha_corte=date(2026, 6, 15),
        direccion_prorrateo=DireccionProrrateo.HACIA_ATRAS,
    )


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
            escribano_nombre="Monica",
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

    monica = next(e for e in resumen.por_escribano if e.escribano_nombre == "Monica")
    assert monica.escrituras == []
    assert monica.total == Decimal("0.00")


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


@pytest.mark.asyncio
async def test_neto_impuestos_cobro_sin_egreso_es_positivo(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
    cleanup_escrituras: list,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("services.pago_impuesto_cliente_service.publish", AsyncMock())
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session,
            seeded_config,
            escribano_nombre="Costanza",
            created_at=_dt(11),
        )
        cleanup_escrituras.append(escritura.id)
        impuesto = await create_impuesto(session, escritura.id, _impuesto_input())
        from services.pago_impuesto_cliente_service import upsert_pago

        await upsert_pago(
            session,
            escritura.id,
            impuesto.id,
            PagoImpuestoInput(monto=Decimal("50000.00"), fecha=_payment_date()),
        )
        resumen = await get_liquidacion_mensual(session, TEST_YEAR, TEST_MONTH)

    costanza = next(e for e in resumen.por_escribano if e.escribano_nombre == "Costanza")
    item = costanza.escrituras[0]
    assert item.neto_impuestos == Decimal("50000.00")
    assert item.monto_cobrado == Decimal("0.00")
    assert costanza.total == Decimal("50000.00")


@pytest.mark.asyncio
async def test_neto_impuestos_egreso_sin_cobro_es_negativo(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
    cleanup_escrituras: list,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("services.pago_impuesto_escribania_service.publish", AsyncMock())
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session,
            seeded_config,
            escribano_nombre="Gabriel",
            created_at=_dt(12),
        )
        cleanup_escrituras.append(escritura.id)
        impuesto = await create_impuesto(session, escritura.id, _impuesto_input())
        from services.pago_impuesto_escribania_service import upsert_pago

        await upsert_pago(
            session,
            escritura.id,
            impuesto.id,
            PagoImpuestoInput(monto=Decimal("30000.00"), fecha=_payment_date(18)),
        )
        resumen = await get_liquidacion_mensual(session, TEST_YEAR, TEST_MONTH)

    gabriel = next(e for e in resumen.por_escribano if e.escribano_nombre == "Gabriel")
    assert gabriel.escrituras[0].neto_impuestos == Decimal("-30000.00")
    assert gabriel.total == Decimal("-30000.00")


@pytest.mark.asyncio
async def test_neto_impuestos_compensados_es_cero(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
    cleanup_escrituras: list,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("services.pago_impuesto_cliente_service.publish", AsyncMock())
    monkeypatch.setattr("services.pago_impuesto_escribania_service.publish", AsyncMock())
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session,
            seeded_config,
            escribano_nombre="Monica",
            created_at=_dt(13),
        )
        cleanup_escrituras.append(escritura.id)
        impuesto = await create_impuesto(session, escritura.id, _impuesto_input())
        from services.pago_impuesto_cliente_service import upsert_pago as upsert_cliente
        from services.pago_impuesto_escribania_service import upsert_pago as upsert_escribania

        await upsert_cliente(
            session,
            escritura.id,
            impuesto.id,
            PagoImpuestoInput(monto=Decimal("40000.00"), fecha=_payment_date(14)),
        )
        await upsert_escribania(
            session,
            escritura.id,
            impuesto.id,
            PagoImpuestoInput(monto=Decimal("40000.00"), fecha=_payment_date(16)),
        )
        resumen = await get_liquidacion_mensual(session, TEST_YEAR, TEST_MONTH)

    monica = next(e for e in resumen.por_escribano if e.escribano_nombre == "Monica")
    assert monica.escrituras[0].neto_impuestos == Decimal("0.00")
    assert monica.total == Decimal("0.00")


@pytest.mark.asyncio
async def test_neto_impuestos_suma_dos_movimientos_mismo_mes(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
    cleanup_escrituras: list,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("services.pago_impuesto_cliente_service.publish", AsyncMock())
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session,
            seeded_config,
            escribano_nombre="Costanza",
            created_at=_dt(14),
        )
        cleanup_escrituras.append(escritura.id)
        impuesto_api = await create_impuesto(session, escritura.id, _impuesto_input())
        impuesto_tgi = await create_impuesto(
            session,
            escritura.id,
            ImpuestoInput(
                tipo=TipoImpuesto.TGI,
                monto_total=Decimal("8000.00"),
                periodo_inicio=date(2026, 5, 1),
                periodo_fin=date(2026, 6, 30),
                fecha_corte=date(2026, 6, 15),
                direccion_prorrateo=DireccionProrrateo.HACIA_ATRAS,
            ),
        )
        from services.pago_impuesto_cliente_service import upsert_pago

        await upsert_pago(
            session,
            escritura.id,
            impuesto_api.id,
            PagoImpuestoInput(monto=Decimal("20000.00"), fecha=_payment_date(10)),
        )
        await upsert_pago(
            session,
            escritura.id,
            impuesto_tgi.id,
            PagoImpuestoInput(monto=Decimal("15000.00"), fecha=_payment_date(22)),
        )
        resumen = await get_liquidacion_mensual(session, TEST_YEAR, TEST_MONTH)

    costanza = next(e for e in resumen.por_escribano if e.escribano_nombre == "Costanza")
    assert costanza.escrituras[0].neto_impuestos == Decimal("35000.00")
    assert costanza.total == Decimal("35000.00")


@pytest.mark.asyncio
async def test_close_liquidacion_mensual_no_bloquea_por_balance_impuestos(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
    cleanup_escrituras: list,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("services.pago_impuesto_cliente_service.publish", AsyncMock())
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session,
            seeded_config,
            escribano_nombre="Costanza",
            created_at=_dt(15),
        )
        cleanup_escrituras.append(escritura.id)
        impuesto = await create_impuesto(session, escritura.id, _impuesto_input())
        from services.pago_impuesto_cliente_service import upsert_pago

        await upsert_pago(
            session,
            escritura.id,
            impuesto.id,
            PagoImpuestoInput(monto=Decimal("50000.00"), fecha=_payment_date()),
        )
        await close_liquidacion_mensual(session, TEST_YEAR, TEST_MONTH)

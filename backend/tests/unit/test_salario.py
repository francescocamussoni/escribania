from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock
import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from models.empleado import Empleado
from models.escritura import EstadoEscritura
from models.gasto_extraordinario import GastoExtraordinario
from models.impuesto_escritura import DireccionProrrateo, TipoImpuesto
from models.pago_cliente import PagoCliente
from schemas.impuesto import ImpuestoInput, PagoImpuestoInput
from services.impuesto_service import create_impuesto
from services.salario_service import get_pagos_mensuales
from helpers.escritura_factory import insert_test_escritura

TEST_YEAR = 2030
TEST_MONTH = 7

pytestmark = pytest.mark.usefixtures("isolated_liquidacion_month")


def _dt(day: int) -> datetime:
    return datetime(TEST_YEAR, TEST_MONTH, day, 12, 0, 0, tzinfo=UTC)


def _payment_date(day: int = 15) -> date:
    return date(TEST_YEAR, TEST_MONTH, day)


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


async def _insert_gasto_extraordinario(
    session: AsyncSession,
    *,
    concepto: str,
    monto: Decimal,
    fecha: date,
) -> GastoExtraordinario:
    gasto = GastoExtraordinario(
        id=uuid.uuid4(),
        concepto=concepto,
        monto=monto,
        fecha=fecha,
    )
    session.add(gasto)
    await session.commit()
    return gasto


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


@pytest.mark.asyncio
async def test_escribano_total_includes_monto_cobrado_and_neto_impuestos(
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
            created_at=_dt(16),
        )
        cleanup_escrituras.append(escritura.id)
        await _insert_pago_cliente(
            session,
            escritura.id,
            monto=Decimal("100000.00"),
            fecha=_payment_date(),
        )
        impuesto = await create_impuesto(session, escritura.id, _impuesto_input())
        from services.pago_impuesto_cliente_service import upsert_pago

        await upsert_pago(
            session,
            escritura.id,
            impuesto.id,
            PagoImpuestoInput(monto=Decimal("25000.00"), fecha=_payment_date(18)),
        )
        pagos = await get_pagos_mensuales(session, TEST_YEAR, TEST_MONTH)

    costanza = next(p for p in pagos.escribanos if p.nombre == "Costanza")
    assert costanza.escrituras[0].monto_cobrado == Decimal("100000.00")
    assert costanza.escrituras[0].neto_impuestos == Decimal("25000.00")
    assert costanza.monto_total == Decimal("125000.00")


@pytest.mark.asyncio
async def test_deduccion_gastos_extraordinarios_reparto_equitativo(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session,
            seeded_config,
            escribano_nombre="Costanza",
            created_at=_dt(17),
        )
        cleanup_escrituras.append(escritura.id)
        await _insert_pago_cliente(
            session,
            escritura.id,
            monto=Decimal("250000.00"),
            fecha=_payment_date(),
        )
        await _insert_gasto_extraordinario(
            session,
            concepto="Gastos oficina",
            monto=Decimal("300000.00"),
            fecha=_payment_date(),
        )
        pagos = await get_pagos_mensuales(session, TEST_YEAR, TEST_MONTH)

    assert pagos.total_gastos_extraordinarios == Decimal("300000.00")
    assert pagos.advertencia_reparto is None
    deducciones = {p.nombre: p.deduccion_gastos_extraordinarios for p in pagos.escribanos}
    assert deducciones == {
        "Costanza": Decimal("100000.00"),
        "Gabriel": Decimal("100000.00"),
        "Monica": Decimal("100000.00"),
    }
    costanza = next(p for p in pagos.escribanos if p.nombre == "Costanza")
    assert costanza.monto_neto == Decimal("150000.00")


@pytest.mark.asyncio
async def test_monto_neto_equals_monto_total_minus_deduccion(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        await _insert_gasto_extraordinario(
            session,
            concepto="Varios",
            monto=Decimal("300000.00"),
            fecha=_payment_date(),
        )
        pagos = await get_pagos_mensuales(session, TEST_YEAR, TEST_MONTH)

    for escribano in pagos.escribanos:
        assert escribano.monto_neto == escribano.monto_total - escribano.deduccion_gastos_extraordinarios


@pytest.mark.asyncio
async def test_advertencia_reparto_sin_escribanos_activos(
    session_factory: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _no_escribanos(_session: AsyncSession) -> list:
        return []

    monkeypatch.setattr("services.salario_service.list_active_escribanos", _no_escribanos)
    monkeypatch.setattr("services.liquidacion_service.list_active", _no_escribanos)

    async with session_factory() as session:
        await _insert_gasto_extraordinario(
            session,
            concepto="Sin reparto",
            monto=Decimal("50000.00"),
            fecha=_payment_date(),
        )
        pagos = await get_pagos_mensuales(session, TEST_YEAR, TEST_MONTH)

    assert pagos.total_gastos_extraordinarios == Decimal("50000.00")
    assert pagos.advertencia_reparto is not None
    assert pagos.escribanos == []

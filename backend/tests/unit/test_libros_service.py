from datetime import UTC, date, datetime
from decimal import Decimal
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from models.escritura import EstadoEscritura
from models.pago_cliente import PagoCliente
from models.pago_colegio import PagoColegio
from services.libros_service import get_libro_entrada, get_libro_salida
from helpers.escritura_factory import insert_test_escritura

TEST_YEAR = 2026
TEST_MONTH = 7
PAYMENT_DAY = 15

pytestmark = pytest.mark.usefixtures("isolated_liquidacion_month")


def _dt(day: int) -> datetime:
    return datetime(TEST_YEAR, TEST_MONTH, day, 12, 0, 0, tzinfo=UTC)


def _payment_date(day: int = PAYMENT_DAY) -> date:
    return date(TEST_YEAR, TEST_MONTH, day)


def _prev_month_payment_date(day: int = 12) -> date:
    return date(TEST_YEAR, TEST_MONTH - 1, day)


async def _insert_pago_cliente(
    session: AsyncSession,
    escritura_id: uuid.UUID,
    *,
    concepto: str,
    monto: Decimal,
    fecha: date,
) -> PagoCliente:
    pago = PagoCliente(
        id=uuid.uuid4(),
        escritura_id=escritura_id,
        concepto=concepto,
        monto=monto,
        fecha=fecha,
    )
    session.add(pago)
    await session.commit()
    return pago


async def _insert_pago_colegio(
    session: AsyncSession,
    escritura_id: uuid.UUID,
    *,
    concepto: str,
    monto: Decimal,
    fecha: date,
) -> PagoColegio:
    pago = PagoColegio(
        id=uuid.uuid4(),
        escritura_id=escritura_id,
        concepto=concepto,
        monto=monto,
        fecha=fecha,
    )
    session.add(pago)
    await session.commit()
    return pago


@pytest.mark.asyncio
async def test_libro_entrada_only_includes_pagos_cliente_del_mes(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session,
            seeded_config,
            created_at=_dt(4),
            nombre="Entrada Test",
        )
        cleanup_escrituras.append(escritura.id)
        await _insert_pago_cliente(
            session,
            escritura.id,
            concepto="Anticipo cliente",
            monto=Decimal("100000.00"),
            fecha=_payment_date(),
        )
        libro = await get_libro_entrada(session, TEST_YEAR, TEST_MONTH)

    conceptos = {linea.concepto for linea in libro.lineas}
    assert conceptos == {"Anticipo cliente"}
    assert "Honorarios Profesionales" not in conceptos
    assert "Certificaci?n" not in conceptos


@pytest.mark.asyncio
async def test_libro_entrada_total_matches_sum_of_pagos(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(session, seeded_config, created_at=_dt(6))
        cleanup_escrituras.append(escritura.id)
        await _insert_pago_cliente(
            session,
            escritura.id,
            concepto="Dep?sito",
            monto=Decimal("50000.00"),
            fecha=_payment_date(),
        )
        await _insert_pago_cliente(
            session,
            escritura.id,
            concepto="Segundo pago",
            monto=Decimal("25000.00"),
            fecha=_payment_date(20),
        )
        libro = await get_libro_entrada(session, TEST_YEAR, TEST_MONTH)

    expected = Decimal("75000.00")
    assert libro.total == expected
    assert sum((linea.monto for linea in libro.lineas), Decimal("0")) == expected


@pytest.mark.asyncio
async def test_libro_entrada_lines_have_traceability(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session,
            seeded_config,
            created_at=_dt(7),
            nombre="Trazabilidad Entrada",
        )
        cleanup_escrituras.append(escritura.id)
        await _insert_pago_cliente(
            session,
            escritura.id,
            concepto="Pago trazable",
            monto=Decimal("1000.00"),
            fecha=_payment_date(10),
        )
        libro = await get_libro_entrada(session, TEST_YEAR, TEST_MONTH)

    assert len(libro.lineas) == 1
    linea = libro.lineas[0]
    assert linea.escritura_id == str(escritura.id)
    assert linea.escritura_nombre == "Trazabilidad Entrada"
    assert linea.fecha_pago == _payment_date(10)


@pytest.mark.asyncio
async def test_libro_entrada_excludes_pagos_from_previous_month(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session,
            seeded_config,
            created_at=_prev_month_payment_date(),
            nombre="Mes Anterior",
        )
        cleanup_escrituras.append(escritura.id)
        await _insert_pago_cliente(
            session,
            escritura.id,
            concepto="Pago viejo",
            monto=Decimal("99999.00"),
            fecha=_prev_month_payment_date(),
        )
        libro = await get_libro_entrada(session, TEST_YEAR, TEST_MONTH)

    assert libro.lineas == []
    assert libro.total == Decimal("0.00")


@pytest.mark.asyncio
async def test_libro_entrada_resumen_deudas_for_open_escrituras_with_saldo(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    async with session_factory() as session:
        con_deuda = await insert_test_escritura(
            session,
            seeded_config,
            created_at=_dt(8),
            estado=EstadoEscritura.ABIERTA,
            nombre="Con deuda",
        )
        pagada = await insert_test_escritura(
            session,
            seeded_config,
            created_at=_dt(9),
            estado=EstadoEscritura.ABIERTA,
            nombre="Pagada parcial",
        )
        cleanup_escrituras.extend([con_deuda.id, pagada.id])
        await _insert_pago_cliente(
            session,
            pagada.id,
            concepto="Anticipo",
            monto=Decimal("400000.00"),
            fecha=_payment_date(),
        )
        libro = await get_libro_entrada(session, TEST_YEAR, TEST_MONTH)

    deuda_ids = {item.escritura_id for item in libro.resumen_deudas}
    assert str(con_deuda.id) in deuda_ids
    assert str(pagada.id) in deuda_ids
    con_deuda_item = next(
        item for item in libro.resumen_deudas if item.escritura_id == str(con_deuda.id)
    )
    assert con_deuda_item.saldo_pendiente == con_deuda_item.costo_total
    assert con_deuda_item.total_pagado == Decimal("0.00")


@pytest.mark.asyncio
async def test_libro_entrada_resumen_deudas_excludes_closed_escrituras(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    async with session_factory() as session:
        cerrada = await insert_test_escritura(
            session,
            seeded_config,
            created_at=_dt(10),
            estado=EstadoEscritura.CERRADA,
            nombre="Cerrada",
        )
        cleanup_escrituras.append(cerrada.id)
        libro = await get_libro_entrada(session, TEST_YEAR, TEST_MONTH)

    assert all(item.escritura_id != str(cerrada.id) for item in libro.resumen_deudas)


@pytest.mark.asyncio
async def test_libro_salida_only_includes_pagos_colegio_del_mes(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(session, seeded_config, created_at=_dt(10))
        cleanup_escrituras.append(escritura.id)
        await _insert_pago_colegio(
            session,
            escritura.id,
            concepto="Aporte Colegio",
            monto=Decimal("25000.00"),
            fecha=_payment_date(),
        )
        libro = await get_libro_salida(session, TEST_YEAR, TEST_MONTH)

    conceptos = {linea.concepto for linea in libro.lineas}
    assert conceptos == {"Aporte Colegio"}
    assert "Sellos Fiscales" not in conceptos
    assert "Honorarios Profesionales" not in conceptos


@pytest.mark.asyncio
async def test_libro_salida_excludes_pagos_cliente(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(session, seeded_config, created_at=_dt(11))
        cleanup_escrituras.append(escritura.id)
        await _insert_pago_cliente(
            session,
            escritura.id,
            concepto="Solo Entrada",
            monto=Decimal("1000.00"),
            fecha=_payment_date(),
        )
        libro = await get_libro_salida(session, TEST_YEAR, TEST_MONTH)

    assert libro.lineas == []
    assert libro.total == Decimal("0.00")


@pytest.mark.asyncio
async def test_libro_salida_total_matches_sum_of_pagos(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(session, seeded_config, created_at=_dt(12))
        cleanup_escrituras.append(escritura.id)
        await _insert_pago_colegio(
            session,
            escritura.id,
            concepto="Pago 1",
            monto=Decimal("30000.00"),
            fecha=_payment_date(),
        )
        await _insert_pago_colegio(
            session,
            escritura.id,
            concepto="Pago 2",
            monto=Decimal("15000.00"),
            fecha=_payment_date(22),
        )
        libro = await get_libro_salida(session, TEST_YEAR, TEST_MONTH)

    assert libro.total == Decimal("45000.00")
    assert sum((linea.monto for linea in libro.lineas), Decimal("0")) == libro.total


@pytest.mark.asyncio
async def test_libro_salida_lines_have_traceability(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session,
            seeded_config,
            created_at=_dt(13),
            nombre="Trazabilidad Salida",
        )
        cleanup_escrituras.append(escritura.id)
        await _insert_pago_colegio(
            session,
            escritura.id,
            concepto="Colegio trazable",
            monto=Decimal("5000.00"),
            fecha=_payment_date(18),
        )
        libro = await get_libro_salida(session, TEST_YEAR, TEST_MONTH)

    assert len(libro.lineas) == 1
    linea = libro.lineas[0]
    assert linea.escritura_id == str(escritura.id)
    assert linea.escritura_nombre == "Trazabilidad Salida"
    assert linea.fecha_pago == _payment_date(18)


@pytest.mark.asyncio
async def test_libro_salida_excludes_pagos_from_previous_month(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(session, seeded_config, created_at=_dt(14))
        cleanup_escrituras.append(escritura.id)
        await _insert_pago_colegio(
            session,
            escritura.id,
            concepto="Pago viejo",
            monto=Decimal("80000.00"),
            fecha=_prev_month_payment_date(),
        )
        libro = await get_libro_salida(session, TEST_YEAR, TEST_MONTH)

    assert libro.lineas == []
    assert libro.total == Decimal("0.00")

from datetime import UTC, date, datetime
from decimal import Decimal
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from models.escritura import EstadoEscritura
from models.gasto_adicional import DireccionGasto, GastoAdicional
from services.libros_service import get_libro_entrada, get_libro_salida
from helpers.escritura_factory import (
    CANONICAL_CERTIFICACION,
    CANONICAL_HONORARIO,
    CANONICAL_SUBTOTAL,
    insert_test_escritura,
)

TEST_YEAR = 2026
TEST_MONTH = 7

CANONICAL_IMPUESTOS_TOTAL = Decimal("5311489.50")
CANONICAL_LEYES_TOTAL = Decimal("1532857.00")
CANONICAL_GASTOS_ADMIN_TOTAL = Decimal("95444.77")
CANONICAL_SALIDA_TOTAL = (
    CANONICAL_IMPUESTOS_TOTAL + CANONICAL_LEYES_TOTAL + CANONICAL_GASTOS_ADMIN_TOTAL
)

pytestmark = pytest.mark.usefixtures("isolated_liquidacion_month")


def _dt(day: int) -> datetime:
    return datetime(TEST_YEAR, TEST_MONTH, day, 12, 0, 0, tzinfo=UTC)


def _prev_month_dt(day: int) -> datetime:
    return datetime(TEST_YEAR, TEST_MONTH - 1, day, 12, 0, 0, tzinfo=UTC)


async def _insert_gasto(
    session: AsyncSession,
    escritura_id: uuid.UUID,
    *,
    concepto: str,
    monto: Decimal,
    direccion: DireccionGasto,
) -> GastoAdicional:
    gasto = GastoAdicional(
        id=uuid.uuid4(),
        escritura_id=escritura_id,
        concepto=concepto,
        monto=monto,
        direccion=direccion,
        fecha=date(TEST_YEAR, TEST_MONTH, 15),
    )
    session.add(gasto)
    await session.commit()
    return gasto


@pytest.mark.asyncio
async def test_libro_entrada_includes_honorarios_certificacion_and_gastos_entrada(
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
        await _insert_gasto(
            session,
            escritura.id,
            concepto="Anticipo cliente",
            monto=Decimal("100000.00"),
            direccion=DireccionGasto.ENTRADA,
        )
        libro = await get_libro_entrada(session, TEST_YEAR, TEST_MONTH)

    conceptos = {linea.concepto for linea in libro.lineas}
    assert "Honorarios Profesionales" in conceptos
    assert "Certificación" in conceptos
    assert "Anticipo cliente" in conceptos
    assert "Sellos Fiscales" not in conceptos
    assert "Ing. Brutos (3‰)" not in conceptos


@pytest.mark.asyncio
async def test_libro_entrada_total_matches_sum_of_lineas(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(session, seeded_config, created_at=_dt(6))
        cleanup_escrituras.append(escritura.id)
        await _insert_gasto(
            session,
            escritura.id,
            concepto="Depósito",
            monto=Decimal("50000.00"),
            direccion=DireccionGasto.ENTRADA,
        )
        libro = await get_libro_entrada(session, TEST_YEAR, TEST_MONTH)

    expected = CANONICAL_SUBTOTAL + Decimal("50000.00")
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
        libro = await get_libro_entrada(session, TEST_YEAR, TEST_MONTH)

    for linea in libro.lineas:
        assert linea.escritura_id == str(escritura.id)
        assert linea.escritura_nombre == "Trazabilidad Entrada"
        assert linea.fecha_escritura == _dt(7).date()


@pytest.mark.asyncio
async def test_libro_entrada_includes_open_and_closed_escrituras_in_month(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    async with session_factory() as session:
        abierta = await insert_test_escritura(
            session,
            seeded_config,
            created_at=_dt(8),
            estado=EstadoEscritura.ABIERTA,
            nombre="Abierta",
        )
        cerrada = await insert_test_escritura(
            session,
            seeded_config,
            created_at=_dt(9),
            estado=EstadoEscritura.CERRADA,
            nombre="Cerrada",
        )
        cleanup_escrituras.extend([abierta.id, cerrada.id])
        libro = await get_libro_entrada(session, TEST_YEAR, TEST_MONTH)

    nombres = {linea.escritura_nombre for linea in libro.lineas}
    assert {"Abierta", "Cerrada"}.issubset(nombres)


@pytest.mark.asyncio
async def test_libro_entrada_excludes_previous_month_escrituras(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session,
            seeded_config,
            created_at=_prev_month_dt(12),
            nombre="Mes Anterior",
        )
        cleanup_escrituras.append(escritura.id)
        libro = await get_libro_entrada(session, TEST_YEAR, TEST_MONTH)

    assert all(linea.escritura_id != str(escritura.id) for linea in libro.lineas)
    assert libro.total == Decimal("0.00")


@pytest.mark.asyncio
async def test_libro_entrada_canonical_fixture_total(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(session, seeded_config, created_at=_dt(2))
        cleanup_escrituras.append(escritura.id)
        libro = await get_libro_entrada(session, TEST_YEAR, TEST_MONTH)

    honorario = next(
        linea for linea in libro.lineas if linea.concepto == "Honorarios Profesionales"
    )
    certificacion = next(linea for linea in libro.lineas if linea.concepto == "Certificación")
    assert honorario.monto == CANONICAL_HONORARIO
    assert certificacion.monto == CANONICAL_CERTIFICACION
    assert libro.total == CANONICAL_SUBTOTAL


@pytest.mark.asyncio
async def test_libro_salida_includes_individual_items_not_honorarios(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(session, seeded_config, created_at=_dt(10))
        cleanup_escrituras.append(escritura.id)
        await _insert_gasto(
            session,
            escritura.id,
            concepto="Pago proveedor",
            monto=Decimal("25000.00"),
            direccion=DireccionGasto.SALIDA,
        )
        libro = await get_libro_salida(session, TEST_YEAR, TEST_MONTH)

    conceptos = {linea.concepto for linea in libro.lineas}
    assert "Sellos Fiscales" in conceptos
    assert "Inscripción" in conceptos
    assert "Honorarios Profesionales" not in conceptos
    assert "Certificación" not in conceptos
    assert "Pago proveedor" in conceptos


@pytest.mark.asyncio
async def test_libro_salida_excludes_gastos_entrada(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(session, seeded_config, created_at=_dt(11))
        cleanup_escrituras.append(escritura.id)
        await _insert_gasto(
            session,
            escritura.id,
            concepto="Solo Entrada",
            monto=Decimal("1000.00"),
            direccion=DireccionGasto.ENTRADA,
        )
        libro = await get_libro_salida(session, TEST_YEAR, TEST_MONTH)

    assert all(linea.concepto != "Solo Entrada" for linea in libro.lineas)


@pytest.mark.asyncio
async def test_libro_salida_total_matches_sum_of_lineas(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(session, seeded_config, created_at=_dt(12))
        cleanup_escrituras.append(escritura.id)
        await _insert_gasto(
            session,
            escritura.id,
            concepto="Egreso extra",
            monto=Decimal("30000.00"),
            direccion=DireccionGasto.SALIDA,
        )
        libro = await get_libro_salida(session, TEST_YEAR, TEST_MONTH)

    assert libro.total == CANONICAL_SALIDA_TOTAL + Decimal("30000.00")
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
        libro = await get_libro_salida(session, TEST_YEAR, TEST_MONTH)

    assert libro.lineas
    for linea in libro.lineas:
        assert linea.escritura_id == str(escritura.id)
        assert linea.escritura_nombre == "Trazabilidad Salida"


@pytest.mark.asyncio
async def test_libro_salida_canonical_impuestos_subtotal(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(session, seeded_config, created_at=_dt(14))
        cleanup_escrituras.append(escritura.id)
        libro = await get_libro_salida(session, TEST_YEAR, TEST_MONTH)

    impuestos_labels = {"Ing. Brutos (3‰)", "Sellos Fiscales", "Tasa 7.5‰", "Firma Impuestos"}
    impuestos_total = sum(
        (linea.monto for linea in libro.lineas if linea.concepto in impuestos_labels),
        Decimal("0"),
    )
    assert impuestos_total == CANONICAL_IMPUESTOS_TOTAL
    assert libro.total == CANONICAL_SALIDA_TOTAL

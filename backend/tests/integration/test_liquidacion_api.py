from datetime import UTC, datetime
from decimal import Decimal

import pytest
from httpx import AsyncClient

from models.escritura import EstadoEscritura
from helpers.escritura_factory import CANONICAL_SUBTOTAL, insert_test_escritura

TEST_YEAR = 2026
TEST_MONTH = 7

pytestmark = pytest.mark.usefixtures("isolated_liquidacion_month")


def _dt(day: int) -> datetime:
    return datetime(TEST_YEAR, TEST_MONTH, day, 12, 0, 0, tzinfo=UTC)


def _prev_month_dt(day: int) -> datetime:
    return datetime(TEST_YEAR, TEST_MONTH - 1, day, 12, 0, 0, tzinfo=UTC)


@pytest.mark.asyncio
async def test_get_liquidacion_returns_resumen(
    auth_client: AsyncClient,
    db_session,
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    e1 = await insert_test_escritura(
        db_session,
        seeded_config,
        escribano_nombre="Costanza",
        created_at=_dt(3),
    )
    e2 = await insert_test_escritura(
        db_session,
        seeded_config,
        escribano_nombre="Gabriel",
        created_at=_dt(7),
        estado=EstadoEscritura.CERRADA,
    )
    prev = await insert_test_escritura(
        db_session,
        seeded_config,
        escribano_nombre="Victoria",
        created_at=_prev_month_dt(1),
        estado=EstadoEscritura.CERRADA,
    )
    cleanup_escrituras.extend([e1.id, e2.id, prev.id])

    response = await auth_client.get(
        "/api/v1/liquidacion",
        params={"anio": TEST_YEAR, "mes": TEST_MONTH},
    )
    assert response.status_code == 200

    body = response.json()
    assert body["anio"] == TEST_YEAR
    assert body["mes"] == TEST_MONTH
    assert body["total_costanza"] == str(CANONICAL_SUBTOTAL)
    assert body["total_gabriel"] == str(CANONICAL_SUBTOTAL)
    assert body["total_victoria"] == "0.00"
    assert body["total_global"] == str(CANONICAL_SUBTOTAL * 2)

    por_escribano = {item["escribano_nombre"]: item for item in body["por_escribano"]}
    assert len(por_escribano["Costanza"]["escrituras"]) == 1
    assert por_escribano["Costanza"]["escrituras"][0]["escritura_id"] == str(e1.id)
    assert por_escribano["Gabriel"]["escrituras"][0]["escritura_id"] == str(e2.id)
    assert por_escribano["Victoria"]["escrituras"] == []


@pytest.mark.asyncio
async def test_get_salarios_returns_escribanos_and_secretarias(
    auth_client: AsyncClient,
    db_session,
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    from sqlalchemy import select

    from models.empleado import Empleado

    escritura = await insert_test_escritura(
        db_session,
        seeded_config,
        escribano_nombre="Costanza",
        created_at=_dt(4),
    )
    cleanup_escrituras.append(escritura.id)
    empleados = list((await db_session.execute(select(Empleado))).scalars().all())

    response = await auth_client.get(
        "/api/v1/salarios",
        params={"anio": TEST_YEAR, "mes": TEST_MONTH},
    )
    assert response.status_code == 200

    body = response.json()
    costanza = next(item for item in body["escribanos"] if item["nombre"] == "Costanza")
    assert costanza["monto_total"] == str(CANONICAL_SUBTOTAL)
    assert len(body["secretarias"]) == len(empleados)
    expected_total = sum((empleado.sueldo for empleado in empleados), Decimal("0.00"))
    assert body["secretarias"][0]["base_total"] == str(expected_total)

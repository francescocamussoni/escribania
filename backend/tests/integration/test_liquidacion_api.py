from datetime import UTC, datetime
from decimal import Decimal

import pytest
from httpx import AsyncClient

from models.escritura import Escribano, EstadoEscritura
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
    db_engine,
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        e1 = await insert_test_escritura(
            session,
            seeded_config,
            escribano=Escribano.COSTANZA,
            created_at=_dt(3),
        )
        e2 = await insert_test_escritura(
            session,
            seeded_config,
            escribano=Escribano.GABRIEL,
            created_at=_dt(7),
            estado=EstadoEscritura.CERRADA,
        )
        prev = await insert_test_escritura(
            session,
            seeded_config,
            escribano=Escribano.VICTORIA,
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

    por_escribano = {item["escribano"]: item for item in body["por_escribano"]}
    assert len(por_escribano["costanza"]["escrituras"]) == 1
    assert por_escribano["costanza"]["escrituras"][0]["escritura_id"] == str(e1.id)
    assert por_escribano["gabriel"]["escrituras"][0]["escritura_id"] == str(e2.id)
    assert por_escribano["victoria"]["escrituras"] == []


@pytest.mark.asyncio
async def test_get_salarios_returns_escribanos_and_secretarias(
    auth_client: AsyncClient,
    db_engine,
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session,
            seeded_config,
            escribano=Escribano.COSTANZA,
            created_at=_dt(9),
        )
        cleanup_escrituras.append(escritura.id)

    response = await auth_client.get(
        "/api/v1/salarios",
        params={"anio": TEST_YEAR, "mes": TEST_MONTH},
    )
    assert response.status_code == 200

    config = await auth_client.get("/api/v1/configuracion")
    base_total = config.json()["salario_secretarias_total"]
    expected_half = str(Decimal(base_total) / Decimal("2"))

    body = response.json()
    assert body["anio"] == TEST_YEAR
    assert body["mes"] == TEST_MONTH

    costanza = next(e for e in body["escribanos"] if e["nombre"] == "Costanza")
    assert costanza["monto_total"] == str(CANONICAL_SUBTOTAL)
    assert costanza["escrituras"][0]["escritura_id"] == str(escritura.id)

    assert len(body["secretarias"]) == 2
    nombres = {s["nombre"] for s in body["secretarias"]}
    assert nombres == {"Graciela", "Guadalupe"}
    assert all(s["monto"] == expected_half for s in body["secretarias"])
    assert all(s["base_total"] == base_total for s in body["secretarias"])


@pytest.mark.asyncio
async def test_liquidacion_requires_auth(client: AsyncClient, seeded_config) -> None:
    response = await client.get("/api/v1/liquidacion", params={"anio": 2026, "mes": 7})
    assert response.status_code == 401

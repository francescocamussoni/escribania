from datetime import UTC, datetime

import pytest
from httpx import AsyncClient

from helpers.escritura_factory import CANONICAL_SUBTOTAL, canonical_escritura_payload, insert_test_escritura

TEST_YEAR = 2026
TEST_MONTH = 7


def _dt(day: int) -> datetime:
    return datetime(TEST_YEAR, TEST_MONTH, day, 12, 0, 0, tzinfo=UTC)


@pytest.mark.asyncio
async def test_get_libro_entrada_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/libros/entrada")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_libro_entrada_returns_200_with_filter(
    auth_client: AsyncClient,
    db_session,
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    escritura = await insert_test_escritura(
        db_session,
        seeded_config,
        created_at=_dt(5),
        nombre="API Entrada",
    )
    cleanup_escrituras.append(escritura.id)

    response = await auth_client.get(
        "/api/v1/libros/entrada",
        params={"anio": TEST_YEAR, "mes": TEST_MONTH},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["anio"] == TEST_YEAR
    assert body["mes"] == TEST_MONTH
    assert body["total"] == str(CANONICAL_SUBTOTAL)
    assert any(linea["escritura_id"] == str(escritura.id) for linea in body["lineas"])


@pytest.mark.asyncio
async def test_get_libro_entrada_defaults_to_current_month(
    auth_client: AsyncClient,
    db_session,
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    now = datetime.now(UTC)
    escritura = await insert_test_escritura(
        db_session,
        seeded_config,
        created_at=datetime(now.year, now.month, 10, 12, 0, 0, tzinfo=UTC),
    )
    cleanup_escrituras.append(escritura.id)

    response = await auth_client.get("/api/v1/libros/entrada")
    assert response.status_code == 200
    body = response.json()
    assert body["anio"] == now.year
    assert body["mes"] == now.month


@pytest.mark.asyncio
async def test_get_libro_salida_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/libros/salida")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_libro_salida_returns_200_with_structure(
    auth_client: AsyncClient,
    db_session,
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    escritura = await insert_test_escritura(
        db_session,
        seeded_config,
        created_at=_dt(6),
        nombre="API Salida",
    )
    cleanup_escrituras.append(escritura.id)

    response = await auth_client.get(
        "/api/v1/libros/salida",
        params={"anio": TEST_YEAR, "mes": TEST_MONTH},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["anio"] == TEST_YEAR
    assert body["mes"] == TEST_MONTH
    assert body["lineas"]
    linea = body["lineas"][0]
    assert {"escritura_id", "escritura_nombre", "concepto", "monto", "fecha_escritura"} <= linea.keys()
    assert any(item["escritura_id"] == str(escritura.id) for item in body["lineas"])


@pytest.mark.asyncio
async def test_libro_entrada_updates_after_escritura_create_via_api(
    auth_client: AsyncClient,
    seeded_config,
    escribano_ids: dict[str, str],
    cleanup_escrituras: list,
) -> None:
    before = await auth_client.get(
        "/api/v1/libros/entrada",
        params={"anio": TEST_YEAR, "mes": TEST_MONTH},
    )
    assert before.status_code == 200
    count_before = len(before.json()["lineas"])

    created = await auth_client.post(
        "/api/v1/escrituras",
        json=canonical_escritura_payload(
            escribano_ids,
            nombre="Nueva para Libro",
            usd_value="10000.00",
        ),
    )
    assert created.status_code == 201
    cleanup_escrituras.append(created.json()["id"])

    after = await auth_client.get(
        "/api/v1/libros/entrada",
        params={"anio": TEST_YEAR, "mes": TEST_MONTH},
    )
    assert after.status_code == 200
    assert len(after.json()["lineas"]) > count_before

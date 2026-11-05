from datetime import UTC, datetime
from decimal import Decimal

import pytest
from httpx import AsyncClient

from helpers.escritura_factory import canonical_escritura_payload, insert_test_escritura

TEST_YEAR = 2030
TEST_MONTH = 7
PAGO_FECHA = "2030-07-20"


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

    pago = await auth_client.post(
        f"/api/v1/escrituras/{escritura.id}/pagos-cliente",
        json={"monto": "100000.00", "fecha": PAGO_FECHA, "concepto": "Anticipo API"},
    )
    assert pago.status_code == 201

    response = await auth_client.get(
        "/api/v1/libros/entrada",
        params={"anio": TEST_YEAR, "mes": TEST_MONTH},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["anio"] == TEST_YEAR
    assert body["mes"] == TEST_MONTH
    assert "resumen_deudas" in body
    assert any(linea["escritura_id"] == str(escritura.id) for linea in body["lineas"])
    linea = next(item for item in body["lineas"] if item["escritura_id"] == str(escritura.id))
    assert linea["monto"] == "100000.00"
    assert linea["fecha_pago"] == PAGO_FECHA
    assert linea["concepto"] == "Anticipo API"
    assert linea["origen"] == "honorario"


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
    assert "resumen_deudas" in body


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

    pago = await auth_client.post(
        f"/api/v1/escrituras/{escritura.id}/pagos-colegio",
        json={
            "monto": "25000.00",
            "fecha": PAGO_FECHA,
            "concepto": "Colegio API",
            "tipo": "otros",
        },
    )
    assert pago.status_code == 201

    response = await auth_client.get(
        "/api/v1/libros/salida",
        params={"anio": TEST_YEAR, "mes": TEST_MONTH},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["anio"] == TEST_YEAR
    assert body["mes"] == TEST_MONTH
    assert body["lineas"]
    linea = next(item for item in body["lineas"] if item["escritura_id"] == str(escritura.id))
    assert {
        "escritura_id",
        "escritura_nombre",
        "concepto",
        "monto",
        "fecha_pago",
        "origen",
        "tipo_pago",
    } <= linea.keys()
    assert linea["monto"] == "25000.00"
    assert linea["fecha_pago"] == PAGO_FECHA
    assert linea["concepto"] == "Colegio API"
    assert linea["origen"] == "honorario"
    assert linea["tipo_pago"] == "otros"


@pytest.mark.asyncio
async def test_get_libro_salida_excludes_pagos_cliente_and_impuestos(
    auth_client: AsyncClient,
    db_session,
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    escritura = await insert_test_escritura(
        db_session,
        seeded_config,
        created_at=_dt(8),
        nombre="Solo pagos colegio",
    )
    cleanup_escrituras.append(escritura.id)

    pago_cliente = await auth_client.post(
        f"/api/v1/escrituras/{escritura.id}/pagos-cliente",
        json={"monto": "80000.00", "fecha": PAGO_FECHA, "concepto": "Anticipo cliente"},
    )
    assert pago_cliente.status_code == 201

    impuesto = await auth_client.post(
        f"/api/v1/escrituras/{escritura.id}/impuestos",
        json={
            "tipo": "API",
            "monto_total": "10000.00",
            "periodo_inicio": "2030-05-01",
            "periodo_fin": "2030-06-30",
            "fecha_corte": "2030-06-15",
            "direccion_prorrateo": "hacia_atras",
        },
    )
    assert impuesto.status_code == 201
    pago_impuesto = await auth_client.post(
        f"/api/v1/escrituras/{escritura.id}/impuestos/{impuesto.json()['id']}/pago-escribania",
        json={"monto": "5000.00", "fecha": PAGO_FECHA},
    )
    assert pago_impuesto.status_code == 201

    pago_colegio = await auth_client.post(
        f"/api/v1/escrituras/{escritura.id}/pagos-colegio",
        json={"monto": "12000.00", "fecha": PAGO_FECHA, "tipo": "colegio"},
    )
    assert pago_colegio.status_code == 201

    response = await auth_client.get(
        "/api/v1/libros/salida",
        params={"anio": TEST_YEAR, "mes": TEST_MONTH},
    )
    assert response.status_code == 200
    lineas = response.json()["lineas"]
    escritura_lineas = [linea for linea in lineas if linea["escritura_id"] == str(escritura.id)]
    assert len(escritura_lineas) == 1
    assert escritura_lineas[0]["monto"] == "12000.00"
    assert escritura_lineas[0]["tipo_pago"] == "colegio"


@pytest.mark.asyncio
async def test_libro_entrada_updates_after_pago_cliente_via_api(
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
    total_before = before.json()["total"]

    created = await auth_client.post(
        "/api/v1/escrituras",
        json=canonical_escritura_payload(
            escribano_ids,
            nombre="Nueva para Libro",
            usd_value="10000.00",
        ),
    )
    assert created.status_code == 201
    escritura_id = created.json()["id"]
    cleanup_escrituras.append(escritura_id)

    pago = await auth_client.post(
        f"/api/v1/escrituras/{escritura_id}/pagos-cliente",
        json={"monto": "50000.00", "fecha": PAGO_FECHA},
    )
    assert pago.status_code == 201

    after = await auth_client.get(
        "/api/v1/libros/entrada",
        params={"anio": TEST_YEAR, "mes": TEST_MONTH},
    )
    assert after.status_code == 200
    assert Decimal(after.json()["total"]) == Decimal(total_before) + Decimal("50000.00")

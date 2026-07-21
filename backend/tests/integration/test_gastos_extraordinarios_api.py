"""Integration tests for gastos extraordinarios API (WU-009)."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

TEST_YEAR = 2030
TEST_MONTH = 7
PAGO_FECHA = f"{TEST_YEAR}-07-15"

GASTO_PAYLOAD = {
    "concepto": "Celulares",
    "monto": "150000.00",
    "fecha": PAGO_FECHA,
}


@pytest.mark.asyncio
async def test_list_gastos_extraordinarios_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/gastos-extraordinarios")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_list_update_delete_gasto(
    auth_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("services.gasto_extraordinario_service.publish", AsyncMock())

    created = await auth_client.post("/api/v1/gastos-extraordinarios", json=GASTO_PAYLOAD)
    assert created.status_code == 201
    body = created.json()
    gasto_id = body["id"]
    assert body["concepto"] == "Celulares"
    assert body["monto"] == "150000.00"

    listing = await auth_client.get(
        "/api/v1/gastos-extraordinarios",
        params={"anio": TEST_YEAR, "mes": TEST_MONTH},
    )
    assert listing.status_code == 200
    list_body = listing.json()
    assert list_body["total"] == "150000.00"
    assert len(list_body["gastos"]) == 1

    updated = await auth_client.patch(
        f"/api/v1/gastos-extraordinarios/{gasto_id}",
        json={"monto": "175000.00"},
    )
    assert updated.status_code == 200
    assert updated.json()["monto"] == "175000.00"

    deleted = await auth_client.delete(f"/api/v1/gastos-extraordinarios/{gasto_id}")
    assert deleted.status_code == 204

    after = await auth_client.get(
        "/api/v1/gastos-extraordinarios",
        params={"anio": TEST_YEAR, "mes": TEST_MONTH},
    )
    assert after.json()["gastos"] == []


@pytest.mark.asyncio
async def test_create_rejects_invalid_monto(auth_client: AsyncClient) -> None:
    response = await auth_client.post(
        "/api/v1/gastos-extraordinarios",
        json={**GASTO_PAYLOAD, "monto": "0"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_delete_not_found(auth_client: AsyncClient) -> None:
    response = await auth_client.delete(
        "/api/v1/gastos-extraordinarios/00000000-0000-0000-0000-000000000099"
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_post_gasto_refleja_deduccion_en_salarios(
    auth_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("services.gasto_extraordinario_service.publish", AsyncMock())

    created = await auth_client.post(
        "/api/v1/gastos-extraordinarios",
        json={
            "concepto": "Gastos compartidos",
            "monto": "300000.00",
            "fecha": PAGO_FECHA,
        },
    )
    assert created.status_code == 201

    salarios = await auth_client.get(
        "/api/v1/salarios",
        params={"anio": TEST_YEAR, "mes": TEST_MONTH},
    )
    assert salarios.status_code == 200
    body = salarios.json()
    assert body["total_gastos_extraordinarios"] == "300000.00"
    assert body["advertencia_reparto"] is None

    deducciones = {item["nombre"]: item["deduccion_gastos_extraordinarios"] for item in body["escribanos"]}
    assert deducciones == {
        "Costanza": "100000.00",
        "Gabriel": "100000.00",
        "Victoria": "100000.00",
    }
    for item in body["escribanos"]:
        monto_total = Decimal(item["monto_total"])
        deduccion = Decimal(item["deduccion_gastos_extraordinarios"])
        assert Decimal(item["monto_neto"]) == monto_total - deduccion

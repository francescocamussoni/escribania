from decimal import Decimal

import pytest
from httpx import AsyncClient

BASE_PAYLOAD = {
    "usd_value": "105000.00",
    "dolar_mep": "1450.34",
    "dolar_nacion": "1425.00",
}

EXPECTED_FACTURA = {
    "monto_base_mep": "152285700.00",
    "precio_base_nacion": "149625000.00",
    "honorario_principal": "3654856.80",
    "certificacion": "456857.10",
    "suma_hon_cert": "4111713.90",
    "total_leyes_notariales": "1532857.00",
    "total_impuestos": "5311489.50",
    "total_gastos_admin": "95444.77",
    "dif_honorarios": "3618308.23",
    "total_parcial": "3683421.00",
    "total_sin_iva": "9674809.01",
    "iva": "1875257.52",
    "total_factura": "11550066.53",
}

PAGO_FECHA = "2026-07-20"


def _payload(escribano_ids: dict[str, str], *, nombre: str, escribano: str) -> dict[str, str]:
    return {
        **BASE_PAYLOAD,
        "nombre": nombre,
        "escribano_id": escribano_ids[escribano],
    }


def _assert_canonical_factura(factura: dict) -> None:
    for field, expected in EXPECTED_FACTURA.items():
        assert factura[field] == expected, f"{field}: expected {expected}, got {factura[field]}"


def _assert_saldo_abierta_sin_pagos(body: dict) -> None:
    assert body["costo_total"] == EXPECTED_FACTURA["total_factura"]
    assert body["total_pagado"] == "0.00"
    assert body["saldo_pendiente"] == EXPECTED_FACTURA["total_factura"]
    assert body["pagada_al_100"] is False
    assert body["sobrepago"] is False
    assert body["pagos_cliente"] == []
    assert body["pagos_colegio"] == []
    factura = body["factura"]
    assert Decimal(factura["total_factura"]) == Decimal(factura["total_sin_iva"]) + Decimal(
        factura["iva"]
    )


async def _create_escritura(
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    cleanup_escrituras: list,
    *,
    nombre: str = "Compraventa Calle Falsa 123",
    escribano: str = "costanza",
) -> dict:
    response = await auth_client.post(
        "/api/v1/escrituras",
        json=_payload(escribano_ids, nombre=nombre, escribano=escribano),
    )
    assert response.status_code == 201
    body = response.json()
    cleanup_escrituras.append(body["id"])
    return body


async def _pay_full(auth_client: AsyncClient, escritura_id: str, monto: str) -> None:
    response = await auth_client.post(
        f"/api/v1/escrituras/{escritura_id}/pagos-cliente",
        json={"monto": monto, "fecha": PAGO_FECHA},
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_escritura_calculates_factura(
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    body = await _create_escritura(auth_client, escribano_ids, cleanup_escrituras)
    assert body["estado"] == "abierta"
    assert body["escribano_nombre"] == "Costanza"
    _assert_saldo_abierta_sin_pagos(body)
    _assert_canonical_factura(body["factura"])


@pytest.mark.asyncio
async def test_list_escrituras_with_filters(
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    costanza = await _create_escritura(
        auth_client, escribano_ids, cleanup_escrituras, nombre="Escritura Costanza"
    )
    gabriel = await _create_escritura(
        auth_client, escribano_ids, cleanup_escrituras, nombre="Escritura Gabriel", escribano="gabriel"
    )
    gabriel_escribano_id = gabriel["escribano_id"]

    by_escribano = await auth_client.get(
        "/api/v1/escrituras",
        params={"escribano_id": gabriel_escribano_id},
    )
    assert by_escribano.status_code == 200
    gabriel_items = by_escribano.json()
    assert len(gabriel_items) >= 1
    assert all(item["escribano_nombre"] == "Gabriel" for item in gabriel_items)
    assert all("saldo_pendiente" in item for item in gabriel_items)

    by_estado = await auth_client.get("/api/v1/escrituras", params={"estado": "abierta"})
    assert by_estado.status_code == 200
    assert any(item["id"] == costanza["id"] for item in by_estado.json())

    created_at = costanza["created_at"]
    year = int(created_at[0:4])
    month = int(created_at[5:7])
    by_month = await auth_client.get(
        "/api/v1/escrituras",
        params={"anio": year, "mes": month},
    )
    assert by_month.status_code == 200
    assert any(item["id"] == costanza["id"] for item in by_month.json())


@pytest.mark.asyncio
async def test_get_escritura_detail(
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    created = await _create_escritura(auth_client, escribano_ids, cleanup_escrituras)
    escritura_id = created["id"]

    response = await auth_client.get(f"/api/v1/escrituras/{escritura_id}")
    assert response.status_code == 200

    body = response.json()
    assert body["id"] == escritura_id
    assert "factura" in body
    _assert_saldo_abierta_sin_pagos(body)
    _assert_canonical_factura(body["factura"])


@pytest.mark.asyncio
async def test_patch_open_escritura_recalculates(
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    config = await auth_client.get("/api/v1/configuracion")
    honorario_min = Decimal(config.json()["honorario_min"])
    honorario_pct = Decimal(config.json()["honorario_pct"])

    created = await _create_escritura(auth_client, escribano_ids, cleanup_escrituras)
    escritura_id = created["id"]

    response = await auth_client.patch(
        f"/api/v1/escrituras/{escritura_id}",
        json={"usd_value": "10000.00"},
    )
    assert response.status_code == 200

    body = response.json()
    assert body["usd_value"] == "10000.00"
    monto_base = Decimal("10000.00") * Decimal("1450.34")
    expected_honorario = max(monto_base * honorario_pct, honorario_min).quantize(Decimal("0.01"))
    assert Decimal(body["factura"]["honorario_principal"]) == expected_honorario


@pytest.mark.asyncio
async def test_patch_closed_escritura_returns_409(
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    created = await _create_escritura(auth_client, escribano_ids, cleanup_escrituras)
    escritura_id = created["id"]
    await _pay_full(auth_client, escritura_id, created["costo_total"])

    closed = await auth_client.post(f"/api/v1/escrituras/{escritura_id}/close")
    assert closed.status_code == 200
    assert closed.json()["estado"] == "cerrada"
    assert closed.json()["closed_at"] is not None

    response = await auth_client.patch(
        f"/api/v1/escrituras/{escritura_id}",
        json={"nombre": "No debe actualizarse"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_close_escritura_sets_cerrada(
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    created = await _create_escritura(auth_client, escribano_ids, cleanup_escrituras)
    escritura_id = created["id"]
    await _pay_full(auth_client, escritura_id, created["costo_total"])

    response = await auth_client.post(f"/api/v1/escrituras/{escritura_id}/close")
    assert response.status_code == 200

    body = response.json()
    assert body["estado"] == "cerrada"
    assert body["closed_at"] is not None
    assert body["pagada_al_100"] is True


@pytest.mark.asyncio
async def test_add_pago_cliente_to_open_escritura(
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    created = await _create_escritura(auth_client, escribano_ids, cleanup_escrituras)
    escritura_id = created["id"]

    response = await auth_client.post(
        f"/api/v1/escrituras/{escritura_id}/pagos-cliente",
        json={"monto": "50000.00", "fecha": PAGO_FECHA, "concepto": "Anticipo"},
    )
    assert response.status_code == 201
    assert response.json()["concepto"] == "Anticipo"

    detail = await auth_client.get(f"/api/v1/escrituras/{escritura_id}")
    body = detail.json()
    assert len(body["pagos_cliente"]) == 1
    assert body["total_pagado"] == "50000.00"
    assert Decimal(body["saldo_pendiente"]) == Decimal(created["costo_total"]) - Decimal("50000.00")


@pytest.mark.asyncio
async def test_close_escritura_with_saldo_pendiente_returns_409(
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    created = await _create_escritura(auth_client, escribano_ids, cleanup_escrituras)
    escritura_id = created["id"]

    response = await auth_client.post(f"/api/v1/escrituras/{escritura_id}/close")
    assert response.status_code == 409

    body = response.json()["detail"]
    assert body["saldo_pendiente"] == created["costo_total"]
    assert "saldo pendiente" in body["detail"].lower()

    detail = await auth_client.get(f"/api/v1/escrituras/{escritura_id}")
    assert detail.json()["estado"] == "abierta"


@pytest.mark.asyncio
async def test_close_escritura_with_sobrepago_allows_close(
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    created = await _create_escritura(auth_client, escribano_ids, cleanup_escrituras)
    escritura_id = created["id"]
    await _pay_full(auth_client, escritura_id, created["costo_total"])

    patched = await auth_client.patch(
        f"/api/v1/escrituras/{escritura_id}",
        json={"usd_value": "10000.00"},
    )
    assert patched.status_code == 200
    assert patched.json()["sobrepago"] is True
    assert patched.json()["saldo_pendiente"] == "0.00"

    response = await auth_client.post(f"/api/v1/escrituras/{escritura_id}/close")
    assert response.status_code == 200
    assert response.json()["estado"] == "cerrada"


@pytest.mark.asyncio
async def test_escrituras_require_auth(client: AsyncClient, seeded_config) -> None:
    response = await client.get("/api/v1/escrituras")
    assert response.status_code == 401


IMPUESTO_PAYLOAD = {
    "tipo": "API",
    "monto_total": "10000.00",
    "periodo_inicio": "2026-05-01",
    "periodo_fin": "2026-06-30",
    "fecha_corte": "2026-06-15",
    "direccion_prorrateo": "hacia_atras",
}


async def _create_impuesto(auth_client: AsyncClient, escritura_id: str) -> dict:
    response = await auth_client.post(
        f"/api/v1/escrituras/{escritura_id}/impuestos",
        json=IMPUESTO_PAYLOAD,
    )
    assert response.status_code == 201
    return response.json()


@pytest.mark.asyncio
async def test_close_escritura_with_impuesto_balance_returns_409(
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from unittest.mock import AsyncMock

    monkeypatch.setattr("services.pago_impuesto_cliente_service.publish", AsyncMock())
    monkeypatch.setattr("services.pago_impuesto_escribania_service.publish", AsyncMock())

    created = await _create_escritura(auth_client, escribano_ids, cleanup_escrituras)
    escritura_id = created["id"]
    await _pay_full(auth_client, escritura_id, created["costo_total"])
    impuesto = await _create_impuesto(auth_client, escritura_id)

    pago_cliente = await auth_client.post(
        f"/api/v1/escrituras/{escritura_id}/impuestos/{impuesto['id']}/pago-cliente",
        json={"monto": "7540.98", "fecha": PAGO_FECHA},
    )
    assert pago_cliente.status_code == 201
    pago_escribania = await auth_client.post(
        f"/api/v1/escrituras/{escritura_id}/impuestos/{impuesto['id']}/pago-escribania",
        json={"monto": "2459.02", "fecha": PAGO_FECHA},
    )
    assert pago_escribania.status_code == 201

    response = await auth_client.post(f"/api/v1/escrituras/{escritura_id}/close")
    assert response.status_code == 409
    body = response.json()["detail"]
    assert body["code"] == "impuestos_balance_pendiente"
    assert body["balance"] == "5081.96"


@pytest.mark.asyncio
async def test_close_escritura_with_impuesto_sin_pagos_returns_409(
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    created = await _create_escritura(auth_client, escribano_ids, cleanup_escrituras)
    escritura_id = created["id"]
    await _pay_full(auth_client, escritura_id, created["costo_total"])
    await _create_impuesto(auth_client, escritura_id)

    response = await auth_client.post(f"/api/v1/escrituras/{escritura_id}/close")
    assert response.status_code == 409
    body = response.json()["detail"]
    assert body["code"] == "impuestos_pagos_pendientes"
    assert len(body["impuestos_pendientes"]) == 1
    assert body["impuestos_pendientes"][0]["tipo"] == "API"
    assert body["impuestos_pendientes"][0]["falta_cliente"] is True
    assert body["impuestos_pendientes"][0]["falta_escribania"] is True


@pytest.mark.asyncio
async def test_close_escritura_with_impuestos_balanceados_returns_200(
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from unittest.mock import AsyncMock

    monkeypatch.setattr("services.pago_impuesto_cliente_service.publish", AsyncMock())
    monkeypatch.setattr("services.pago_impuesto_escribania_service.publish", AsyncMock())

    created = await _create_escritura(auth_client, escribano_ids, cleanup_escrituras)
    escritura_id = created["id"]
    await _pay_full(auth_client, escritura_id, created["costo_total"])
    impuesto = await _create_impuesto(auth_client, escritura_id)

    pago_cliente = await auth_client.post(
        f"/api/v1/escrituras/{escritura_id}/impuestos/{impuesto['id']}/pago-cliente",
        json={"monto": "7540.98", "fecha": PAGO_FECHA},
    )
    assert pago_cliente.status_code == 201
    pago_escribania = await auth_client.post(
        f"/api/v1/escrituras/{escritura_id}/impuestos/{impuesto['id']}/pago-escribania",
        json={"monto": "7540.98", "fecha": PAGO_FECHA},
    )
    assert pago_escribania.status_code == 201

    response = await auth_client.post(f"/api/v1/escrituras/{escritura_id}/close")
    assert response.status_code == 200
    assert response.json()["estado"] == "cerrada"


@pytest.mark.asyncio
async def test_get_escritura_includes_balance_impuestos(
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    created = await _create_escritura(auth_client, escribano_ids, cleanup_escrituras)
    await _create_impuesto(auth_client, created["id"])

    response = await auth_client.get(f"/api/v1/escrituras/{created['id']}")
    assert response.status_code == 200
    balance = response.json()["balance_impuestos"]
    assert balance is not None
    assert balance["balance"] == "0.00"
    assert balance["puede_cerrar"] is False
    assert len(balance["impuestos_pendientes"]) == 1

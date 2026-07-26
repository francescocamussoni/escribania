from datetime import UTC, date, datetime
from decimal import Decimal
import uuid

import pytest
from httpx import AsyncClient

from models.escritura import EstadoEscritura
from models.pago_cliente import PagoCliente
from helpers.escritura_factory import insert_test_escritura

TEST_YEAR = 2030
TEST_MONTH = 7
PAGO_FECHA = "2030-07-20"


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
        estado=EstadoEscritura.ABIERTA,
    )
    prev = await insert_test_escritura(
        db_session,
        seeded_config,
        escribano_nombre="Monica",
        created_at=_prev_month_dt(1),
        estado=EstadoEscritura.CERRADA,
    )
    cleanup_escrituras.extend([e1.id, e2.id, prev.id])

    pago1 = await auth_client.post(
        f"/api/v1/escrituras/{e1.id}/pagos-cliente",
        json={"monto": "200000.00", "fecha": PAGO_FECHA},
    )
    assert pago1.status_code == 201
    pago2 = await auth_client.post(
        f"/api/v1/escrituras/{e2.id}/pagos-cliente",
        json={"monto": "150000.00", "fecha": PAGO_FECHA},
    )
    assert pago2.status_code == 201
    db_session.add(
        PagoCliente(
            id=uuid.uuid4(),
            escritura_id=prev.id,
            concepto="Pago mes anterior",
            monto=Decimal("999999.00"),
            fecha=date(TEST_YEAR, TEST_MONTH - 1, 15),
        )
    )
    await db_session.commit()

    response = await auth_client.get(
        "/api/v1/liquidacion",
        params={"anio": TEST_YEAR, "mes": TEST_MONTH},
    )
    assert response.status_code == 200

    body = response.json()
    assert body["anio"] == TEST_YEAR
    assert body["mes"] == TEST_MONTH
    assert body["total_costanza"] == "200000.00"
    assert body["total_gabriel"] == "150000.00"
    assert body["total_monica"] == "0.00"
    assert body["total_global"] == "350000.00"

    por_escribano = {item["escribano_nombre"]: item for item in body["por_escribano"]}
    assert len(por_escribano["Costanza"]["escrituras"]) == 1
    assert por_escribano["Costanza"]["escrituras"][0]["escritura_id"] == str(e1.id)
    assert por_escribano["Costanza"]["escrituras"][0]["monto_cobrado"] == "200000.00"
    assert por_escribano["Gabriel"]["escrituras"][0]["escritura_id"] == str(e2.id)
    assert por_escribano["Gabriel"]["escrituras"][0]["monto_cobrado"] == "150000.00"
    assert por_escribano["Monica"]["escrituras"] == []


@pytest.mark.asyncio
async def test_get_liquidacion_includes_neto_impuestos(
    auth_client: AsyncClient,
    db_session,
    seeded_config,
    cleanup_escrituras: list,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from unittest.mock import AsyncMock

    monkeypatch.setattr("services.pago_impuesto_cliente_service.publish", AsyncMock())
    from models.impuesto_escritura import DireccionProrrateo, TipoImpuesto
    from schemas.impuesto import ImpuestoInput, PagoImpuestoInput
    from services.impuesto_service import create_impuesto

    escritura = await insert_test_escritura(
        db_session,
        seeded_config,
        escribano_nombre="Costanza",
        created_at=_dt(8),
        nombre="API Neto Impuestos",
    )
    cleanup_escrituras.append(escritura.id)
    impuesto = await create_impuesto(
        db_session,
        escritura.id,
        ImpuestoInput(
            tipo=TipoImpuesto.API,
            monto_total=Decimal("10000.00"),
            periodo_inicio=date(2026, 5, 1),
            periodo_fin=date(2026, 6, 30),
            fecha_corte=date(2026, 6, 15),
            direccion_prorrateo=DireccionProrrateo.HACIA_ATRAS,
        ),
    )
    from services.pago_impuesto_cliente_service import upsert_pago

    await upsert_pago(
        db_session,
        escritura.id,
        impuesto.id,
        PagoImpuestoInput(monto=Decimal("50000.00"), fecha=date(TEST_YEAR, TEST_MONTH, 20)),
    )

    response = await auth_client.get(
        "/api/v1/liquidacion",
        params={"anio": TEST_YEAR, "mes": TEST_MONTH},
    )
    assert response.status_code == 200
    body = response.json()
    costanza = next(item for item in body["por_escribano"] if item["escribano_nombre"] == "Costanza")
    linea = next(
        item for item in costanza["escrituras"] if item["escritura_id"] == str(escritura.id)
    )
    assert linea["neto_impuestos"] == "50000.00"
    assert linea["monto_cobrado"] == "0.00"
    assert costanza["total"] == "50000.00"


@pytest.mark.asyncio
async def test_close_liquidacion_mensual_with_impuesto_balance_returns_200(
    auth_client: AsyncClient,
    db_session,
    seeded_config,
    cleanup_escrituras: list,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from unittest.mock import AsyncMock

    monkeypatch.setattr("services.pago_impuesto_cliente_service.publish", AsyncMock())
    from models.impuesto_escritura import DireccionProrrateo, TipoImpuesto
    from schemas.impuesto import ImpuestoInput, PagoImpuestoInput
    from services.impuesto_service import create_impuesto
    from services.liquidacion_service import close_liquidacion_mensual

    escritura = await insert_test_escritura(
        db_session,
        seeded_config,
        escribano_nombre="Gabriel",
        created_at=_dt(9),
    )
    cleanup_escrituras.append(escritura.id)
    impuesto = await create_impuesto(
        db_session,
        escritura.id,
        ImpuestoInput(
            tipo=TipoImpuesto.API,
            monto_total=Decimal("10000.00"),
            periodo_inicio=date(2026, 5, 1),
            periodo_fin=date(2026, 6, 30),
            fecha_corte=date(2026, 6, 15),
            direccion_prorrateo=DireccionProrrateo.HACIA_ATRAS,
        ),
    )
    from services.pago_impuesto_cliente_service import upsert_pago

    await upsert_pago(
        db_session,
        escritura.id,
        impuesto.id,
        PagoImpuestoInput(monto=Decimal("50000.00"), fecha=date(TEST_YEAR, TEST_MONTH, 20)),
    )
    await close_liquidacion_mensual(db_session, TEST_YEAR, TEST_MONTH)

    response = await auth_client.get(
        "/api/v1/liquidacion",
        params={"anio": TEST_YEAR, "mes": TEST_MONTH},
    )
    assert response.status_code == 200


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

    pago = await auth_client.post(
        f"/api/v1/escrituras/{escritura.id}/pagos-cliente",
        json={"monto": "300000.00", "fecha": PAGO_FECHA},
    )
    assert pago.status_code == 201

    response = await auth_client.get(
        "/api/v1/salarios",
        params={"anio": TEST_YEAR, "mes": TEST_MONTH},
    )
    assert response.status_code == 200

    body = response.json()
    costanza = next(item for item in body["escribanos"] if item["nombre"] == "Costanza")
    assert costanza["monto_total"] == "300000.00"
    assert costanza["escrituras"][0]["monto_cobrado"] == "300000.00"
    assert len(body["secretarias"]) == len(empleados)
    expected_total = sum((empleado.sueldo for empleado in empleados), Decimal("0.00"))
    assert body["secretarias"][0]["base_total"] == str(expected_total)

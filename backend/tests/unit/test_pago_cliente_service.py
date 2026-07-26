"""TDD unit tests for pago_cliente_service (WU-009 — FAIL FIRST until WU-011)."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from models.escritura import EstadoEscritura
from models.factura_principal import FacturaPrincipal
from schemas.pago_cliente import PagoClienteInput, PagoClienteResponse
from services.escritura_errors import EscrituraClosedError
from services.pago_cliente_service import (
    PagoClienteExcesoSaldoError,
    create_pago,
    sum_pagos,
)
from services.pago_saldo import calc_saldo
from helpers.escritura_factory import insert_test_escritura

CANONICAL_TOTAL_FACTURA = Decimal("11550066.53")

TEST_DATE = date(2026, 7, 20)


def _dt() -> datetime:
    return datetime(2026, 7, 10, 12, 0, 0, tzinfo=UTC)


class TestPagoClienteSchema:
    def test_input_accepts_valid_payload(self) -> None:
        payload = PagoClienteInput.model_validate(
            {"monto": "400000.00", "fecha": "2026-07-20", "concepto": "Anticipo"}
        )
        assert payload.monto == Decimal("400000.00")
        assert payload.fecha == TEST_DATE
        assert payload.concepto == "Anticipo"

    def test_input_default_concepto_empty(self) -> None:
        payload = PagoClienteInput.model_validate({"monto": "100.00", "fecha": "2026-07-20"})
        assert payload.concepto == ""

    def test_input_rejects_extra_fields(self) -> None:
        with pytest.raises(ValidationError):
            PagoClienteInput.model_validate(
                {"monto": "100.00", "fecha": "2026-07-20", "unknown": "x"}
            )

    def test_input_rejects_zero_monto(self) -> None:
        with pytest.raises(ValidationError):
            PagoClienteInput.model_validate({"monto": "0", "fecha": "2026-07-20"})

    def test_input_rejects_negative_monto(self) -> None:
        with pytest.raises(ValidationError):
            PagoClienteInput.model_validate({"monto": "-1.00", "fecha": "2026-07-20"})


async def _costo_total(session: AsyncSession, escritura_id) -> Decimal:
    total = await session.scalar(
        select(FacturaPrincipal.total_factura).where(FacturaPrincipal.escritura_id == escritura_id)
    )
    assert total is not None
    return total


@pytest.mark.asyncio
async def test_create_pago_valido_reduce_saldo(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session, seeded_config, created_at=_dt(), estado=EstadoEscritura.ABIERTA
        )
        costo = await _costo_total(session, escritura.id)
        monto = Decimal("400000.00")

        pago = await create_pago(
            session,
            escritura.id,
            PagoClienteInput(monto=monto, fecha=TEST_DATE, concepto="Anticipo"),
        )

        assert pago.monto == monto
        assert pago.escritura_id == escritura.id
        total_pagado = await sum_pagos(session, escritura.id)
        assert total_pagado == monto
        assert calc_saldo(costo, total_pagado) == costo - monto


@pytest.mark.asyncio
async def test_costo_total_es_total_mas_iva(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session, seeded_config, created_at=_dt(), estado=EstadoEscritura.ABIERTA
        )
        factura = await session.scalar(
            select(FacturaPrincipal).where(FacturaPrincipal.escritura_id == escritura.id)
        )
        assert factura is not None
        costo = await _costo_total(session, escritura.id)

        assert costo == CANONICAL_TOTAL_FACTURA
        assert costo == factura.total_sin_iva + factura.iva
        assert costo == factura.total_factura


@pytest.mark.asyncio
async def test_create_pago_rechaza_monto_mayor_a_saldo(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session, seeded_config, created_at=_dt(), estado=EstadoEscritura.ABIERTA
        )
        costo = await _costo_total(session, escritura.id)

        with pytest.raises(PagoClienteExcesoSaldoError) as exc_info:
            await create_pago(
                session,
                escritura.id,
                PagoClienteInput(monto=costo + Decimal("0.01"), fecha=TEST_DATE),
            )

        assert exc_info.value.saldo_pendiente == costo


@pytest.mark.asyncio
async def test_create_pago_rechaza_escritura_cerrada(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session, seeded_config, created_at=_dt(), estado=EstadoEscritura.CERRADA
        )

        with pytest.raises(EscrituraClosedError):
            await create_pago(
                session,
                escritura.id,
                PagoClienteInput(monto=Decimal("1000.00"), fecha=TEST_DATE),
            )


def test_pago_cliente_service_es_append_only() -> None:
    import services.pago_cliente_service as svc

    for forbidden in ("update_pago", "delete_pago", "modify_pago"):
        assert not hasattr(svc, forbidden), f"{forbidden} must not exist (append-only)"


def test_pago_cliente_response_from_attributes() -> None:
    from types import SimpleNamespace

    row = SimpleNamespace(
        id="00000000-0000-0000-0000-000000000001",
        escritura_id="00000000-0000-0000-0000-000000000002",
        monto=Decimal("100.00"),
        fecha=TEST_DATE,
        concepto="Test",
        created_at=datetime(2026, 7, 20, 12, 0, 0, tzinfo=UTC),
    )
    response = PagoClienteResponse.model_validate(row)
    assert response.monto == Decimal("100.00")

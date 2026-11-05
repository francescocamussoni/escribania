"""TDD unit tests for pago_colegio_service (WU-007 — FAIL FIRST until WU-009)."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from models.escritura import EstadoEscritura
from models.factura_principal import FacturaPrincipal
from models.pago_colegio import TipoPagoEscribania
from schemas.pago_colegio import PagoColegioInput, PagoColegioResponse
from services.escritura_errors import EscrituraClosedError
from services.pago_colegio_service import create_pago, sum_pagos, sum_pagos_colegio
from helpers.escritura_factory import insert_test_escritura

TEST_DATE = date(2026, 7, 20)
CANONICAL_LEYES_NOTARIALES = Decimal("1532857.00")


def _dt() -> datetime:
    return datetime(2026, 7, 10, 12, 0, 0, tzinfo=UTC)


class TestPagoColegioSchema:
    def test_input_accepts_valid_payload_colegio(self) -> None:
        payload = PagoColegioInput.model_validate(
            {
                "monto": "250000.00",
                "fecha": "2026-07-20",
                "concepto": "Aporte Colegio",
                "tipo": "colegio",
            }
        )
        assert payload.monto == Decimal("250000.00")
        assert payload.fecha == TEST_DATE
        assert payload.concepto == "Aporte Colegio"
        assert payload.tipo == TipoPagoEscribania.COLEGIO

    def test_input_default_tipo_colegio(self) -> None:
        payload = PagoColegioInput.model_validate(
            {
                "monto": "100.00",
                "fecha": "2026-07-20",
            }
        )
        assert payload.tipo == TipoPagoEscribania.COLEGIO

    def test_input_default_concepto_empty(self) -> None:
        payload = PagoColegioInput.model_validate(
            {
                "monto": "100.00",
                "fecha": "2026-07-20",
                "tipo": "colegio",
            }
        )
        assert payload.concepto == ""

    def test_input_otros_sin_concepto_rechazado(self) -> None:
        with pytest.raises(ValidationError):
            PagoColegioInput.model_validate(
                {
                    "monto": "100.00",
                    "fecha": "2026-07-20",
                    "tipo": "otros",
                    "concepto": "",
                }
            )

    def test_input_otros_con_concepto_ok(self) -> None:
        payload = PagoColegioInput.model_validate(
            {
                "monto": "100.00",
                "fecha": "2026-07-20",
                "tipo": "otros",
                "concepto": "Gastos varios",
            }
        )
        assert payload.tipo == TipoPagoEscribania.OTROS
        assert payload.concepto == "Gastos varios"

    def test_input_rejects_extra_fields(self) -> None:
        with pytest.raises(ValidationError):
            PagoColegioInput.model_validate(
                {
                    "monto": "100.00",
                    "fecha": "2026-07-20",
                    "tipo": "colegio",
                    "unknown": "x",
                }
            )

    def test_input_rejects_zero_monto(self) -> None:
        with pytest.raises(ValidationError):
            PagoColegioInput.model_validate(
                {
                    "monto": "0",
                    "fecha": "2026-07-20",
                    "tipo": "colegio",
                }
            )

    def test_input_rejects_negative_monto(self) -> None:
        with pytest.raises(ValidationError):
            PagoColegioInput.model_validate(
                {
                    "monto": "-1.00",
                    "fecha": "2026-07-20",
                    "tipo": "colegio",
                }
            )


async def _total_leyes_notariales(session: AsyncSession, escritura_id) -> Decimal:
    total = await session.scalar(
        select(FacturaPrincipal.total_leyes_notariales).where(
            FacturaPrincipal.escritura_id == escritura_id
        )
    )
    assert total is not None
    return total


@pytest.mark.asyncio
async def test_create_pago_ok_con_saldo_cliente_pendiente(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
) -> None:
    """Pago al Colegio no depende del cobro al cliente (US4)."""
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session, seeded_config, created_at=_dt(), estado=EstadoEscritura.ABIERTA
        )
        monto = Decimal("250000.00")

        pago = await create_pago(
            session,
            escritura.id,
            PagoColegioInput(
                monto=monto,
                fecha=TEST_DATE,
                concepto="Aporte Colegio",
                tipo=TipoPagoEscribania.COLEGIO,
            ),
        )

        assert pago.monto == monto
        assert pago.escritura_id == escritura.id
        assert pago.tipo == TipoPagoEscribania.COLEGIO
        total_pagado = await sum_pagos(session, escritura.id)
        assert total_pagado == monto


@pytest.mark.asyncio
async def test_create_pago_otros_con_concepto(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session, seeded_config, created_at=_dt(), estado=EstadoEscritura.ABIERTA
        )
        pago = await create_pago(
            session,
            escritura.id,
            PagoColegioInput(
                monto=Decimal("5000.00"),
                fecha=TEST_DATE,
                tipo=TipoPagoEscribania.OTROS,
                concepto="Certificación extra",
            ),
        )
        assert pago.tipo == TipoPagoEscribania.OTROS
        assert pago.concepto == "Certificación extra"


@pytest.mark.asyncio
async def test_create_pago_no_valida_contra_leyes_notariales_proyectadas(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
) -> None:
    """Monto mayor a total_leyes_notariales debe aceptarse (solo referencia informativa)."""
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session, seeded_config, created_at=_dt(), estado=EstadoEscritura.ABIERTA
        )
        leyes = await _total_leyes_notariales(session, escritura.id)
        assert leyes == CANONICAL_LEYES_NOTARIALES
        monto = leyes + Decimal("500000.00")

        pago = await create_pago(
            session,
            escritura.id,
            PagoColegioInput(
                monto=monto,
                fecha=TEST_DATE,
                concepto="Exceso permitido",
                tipo=TipoPagoEscribania.COLEGIO,
            ),
        )

        assert pago.monto == monto


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
                PagoColegioInput(
                    monto=Decimal("1000.00"),
                    fecha=TEST_DATE,
                    tipo=TipoPagoEscribania.COLEGIO,
                ),
            )


def test_pago_colegio_service_es_append_only() -> None:
    import services.pago_colegio_service as svc

    for forbidden in ("update_pago", "delete_pago", "modify_pago"):
        assert not hasattr(svc, forbidden), f"{forbidden} must not exist (append-only)"


def test_pago_colegio_response_from_attributes() -> None:
    from types import SimpleNamespace

    row = SimpleNamespace(
        id="00000000-0000-0000-0000-000000000001",
        escritura_id="00000000-0000-0000-0000-000000000002",
        monto=Decimal("100.00"),
        fecha=TEST_DATE,
        concepto="Test",
        tipo=TipoPagoEscribania.COLEGIO,
        created_at=datetime(2026, 7, 20, 12, 0, 0, tzinfo=UTC),
    )
    response = PagoColegioResponse.model_validate(row)
    assert response.monto == Decimal("100.00")
    assert response.tipo == TipoPagoEscribania.COLEGIO


@pytest.mark.asyncio
async def test_sum_pagos_colegio_solo_tipo_colegio(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session, seeded_config, created_at=_dt(), estado=EstadoEscritura.ABIERTA
        )
        await create_pago(
            session,
            escritura.id,
            PagoColegioInput(
                monto=Decimal("1000.00"),
                fecha=TEST_DATE,
                tipo=TipoPagoEscribania.COLEGIO,
            ),
        )
        await create_pago(
            session,
            escritura.id,
            PagoColegioInput(
                monto=Decimal("500.00"),
                fecha=TEST_DATE,
                tipo=TipoPagoEscribania.OTROS,
                concepto="Gasto misc",
            ),
        )
        total_colegio = await sum_pagos_colegio(session, escritura.id)
        assert total_colegio == Decimal("1000.00")

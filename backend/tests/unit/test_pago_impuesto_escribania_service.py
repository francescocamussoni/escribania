"""TDD unit tests for pago_impuesto_escribania_service (WU-016)."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from models.escritura import EstadoEscritura
from models.impuesto_escritura import DireccionProrrateo, TipoImpuesto
from models.pago_impuesto_escribania import PagoImpuestoEscribania
from schemas.impuesto import ImpuestoInput, PagoImpuestoInput
from services.escritura_errors import EscrituraClosedError
from services.impuesto_service import create_impuesto, list_impuestos
from services.pago_impuesto_escribania_service import (
    PagoImpuestoEscribaniaNotFoundError,
    delete_pago,
    update_pago,
    upsert_pago,
)
from helpers.escritura_factory import insert_test_escritura

MONTO_TOTAL = Decimal("10000.00")
PERIODO_INICIO = date(2026, 5, 1)
PERIODO_FIN = date(2026, 6, 30)
FECHA_CORTE = date(2026, 6, 15)
MONTO_SUGERIDO_ADELANTE = Decimal("2459.02")
TEST_DATE = date(2026, 7, 20)


def _dt() -> datetime:
    return datetime(2026, 7, 10, 12, 0, 0, tzinfo=UTC)


def _impuesto_input() -> ImpuestoInput:
    return ImpuestoInput(
        tipo=TipoImpuesto.TGI,
        monto_total=MONTO_TOTAL,
        periodo_inicio=PERIODO_INICIO,
        periodo_fin=PERIODO_FIN,
        fecha_corte=FECHA_CORTE,
        direccion_prorrateo=DireccionProrrateo.HACIA_ADELANTE,
    )


class TestPagoImpuestoInputSchema:
    def test_input_accepts_valid_payload(self) -> None:
        payload = PagoImpuestoInput.model_validate({
            "monto": "2459.02",
            "fecha": "2026-07-20",
        })
        assert payload.monto == MONTO_SUGERIDO_ADELANTE
        assert payload.fecha == TEST_DATE

    def test_input_rejects_zero_monto(self) -> None:
        with pytest.raises(ValidationError):
            PagoImpuestoInput.model_validate({"monto": "0", "fecha": "2026-07-20"})

    def test_input_rejects_negative_monto(self) -> None:
        with pytest.raises(ValidationError):
            PagoImpuestoInput.model_validate({"monto": "-1.00", "fecha": "2026-07-20"})


@pytest.mark.asyncio
async def test_upsert_pago_crea_pago_escribania(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session, seeded_config, created_at=_dt(), estado=EstadoEscritura.ABIERTA
        )
        impuesto = await create_impuesto(session, escritura.id, _impuesto_input())
        monkeypatch.setattr(
            "services.pago_impuesto_escribania_service.publish",
            AsyncMock(),
        )

        pago = await upsert_pago(
            session,
            escritura.id,
            impuesto.id,
            PagoImpuestoInput(monto=MONTO_SUGERIDO_ADELANTE, fecha=TEST_DATE),
        )

        assert pago.monto == MONTO_SUGERIDO_ADELANTE
        assert pago.impuesto_id == impuesto.id

        listing = await list_impuestos(session, escritura.id)
        item = next(row for row in listing.impuestos if row.id == impuesto.id)
        assert item.estado_pagos == "solo_escribania"
        assert item.pago_escribania is not None


@pytest.mark.asyncio
async def test_upsert_pago_actualiza_mismo_registro_sin_duplicar(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session, seeded_config, created_at=_dt(), estado=EstadoEscritura.ABIERTA
        )
        impuesto = await create_impuesto(session, escritura.id, _impuesto_input())
        monkeypatch.setattr(
            "services.pago_impuesto_escribania_service.publish",
            AsyncMock(),
        )

        first = await upsert_pago(
            session,
            escritura.id,
            impuesto.id,
            PagoImpuestoInput(monto=MONTO_SUGERIDO_ADELANTE, fecha=TEST_DATE),
        )
        updated_monto = Decimal("3000.00")
        second = await upsert_pago(
            session,
            escritura.id,
            impuesto.id,
            PagoImpuestoInput(monto=updated_monto, fecha=date(2026, 7, 21)),
        )

        assert second.id == first.id
        assert second.monto == updated_monto
        count = await session.scalar(
            select(func.count()).select_from(PagoImpuestoEscribania).where(
                PagoImpuestoEscribania.impuesto_id == impuesto.id
            )
        )
        assert count == 1


@pytest.mark.asyncio
async def test_update_pago_modifica_registro_existente(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session, seeded_config, created_at=_dt(), estado=EstadoEscritura.ABIERTA
        )
        impuesto = await create_impuesto(session, escritura.id, _impuesto_input())
        monkeypatch.setattr(
            "services.pago_impuesto_escribania_service.publish",
            AsyncMock(),
        )
        created = await upsert_pago(
            session,
            escritura.id,
            impuesto.id,
            PagoImpuestoInput(monto=MONTO_SUGERIDO_ADELANTE, fecha=TEST_DATE),
        )

        updated = await update_pago(
            session,
            escritura.id,
            impuesto.id,
            PagoImpuestoInput(monto=Decimal("2600.00"), fecha=date(2026, 7, 22)),
        )

        assert updated.id == created.id
        assert updated.monto == Decimal("2600.00")


@pytest.mark.asyncio
async def test_update_pago_sin_registro_rechazado(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session, seeded_config, created_at=_dt(), estado=EstadoEscritura.ABIERTA
        )
        impuesto = await create_impuesto(session, escritura.id, _impuesto_input())

        with pytest.raises(PagoImpuestoEscribaniaNotFoundError):
            await update_pago(
                session,
                escritura.id,
                impuesto.id,
                PagoImpuestoInput(monto=MONTO_SUGERIDO_ADELANTE, fecha=TEST_DATE),
            )


@pytest.mark.asyncio
async def test_upsert_pago_rechaza_escritura_cerrada(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session, seeded_config, created_at=_dt(), estado=EstadoEscritura.ABIERTA
        )
        impuesto = await create_impuesto(session, escritura.id, _impuesto_input())
        escritura.estado = EstadoEscritura.CERRADA
        await session.commit()

        with pytest.raises(EscrituraClosedError):
            await upsert_pago(
                session,
                escritura.id,
                impuesto.id,
                PagoImpuestoInput(monto=MONTO_SUGERIDO_ADELANTE, fecha=TEST_DATE),
            )


@pytest.mark.asyncio
async def test_delete_pago_quita_registro_y_actualiza_balance(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session, seeded_config, created_at=_dt(), estado=EstadoEscritura.ABIERTA
        )
        impuesto = await create_impuesto(session, escritura.id, _impuesto_input())
        monkeypatch.setattr(
            "services.pago_impuesto_escribania_service.publish",
            AsyncMock(),
        )
        await upsert_pago(
            session,
            escritura.id,
            impuesto.id,
            PagoImpuestoInput(monto=MONTO_SUGERIDO_ADELANTE, fecha=TEST_DATE),
        )

        await delete_pago(session, escritura.id, impuesto.id)

        listing = await list_impuestos(session, escritura.id)
        item = next(row for row in listing.impuestos if row.id == impuesto.id)
        assert item.estado_pagos == "sin_pagos"
        assert item.pago_escribania is None
        assert listing.balance.total_escribania == Decimal("0.00")

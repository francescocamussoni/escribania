"""Unit tests for gasto_extraordinario_service (WU-006)."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from schemas.gasto_extraordinario import GastoExtraordinarioInput, GastoExtraordinarioUpdate
from services.gasto_extraordinario_service import (
    GastoExtraordinarioNotFoundError,
    create_gasto,
    delete_gasto,
    list_by_month,
    update_gasto,
)

TEST_YEAR = 2030
TEST_MONTH = 7
PAGO_FECHA = date(TEST_YEAR, TEST_MONTH, 15)


def _payload(**overrides: object) -> GastoExtraordinarioInput:
    data = {
        "concepto": "Celulares",
        "monto": Decimal("150000.00"),
        "fecha": PAGO_FECHA,
    }
    data.update(overrides)
    return GastoExtraordinarioInput.model_validate(data)


class TestGastoExtraordinarioSchema:
    def test_input_rejects_monto_cero(self) -> None:
        with pytest.raises(ValidationError):
            _payload(monto=Decimal("0"))

    def test_input_rejects_concepto_vacio(self) -> None:
        with pytest.raises(ValidationError):
            _payload(concepto="   ")

    def test_update_rejects_empty_payload(self) -> None:
        with pytest.raises(ValidationError):
            GastoExtraordinarioUpdate.model_validate({})


@pytest.mark.asyncio
async def test_create_y_list_by_month(
    session_factory: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("services.gasto_extraordinario_service.publish", AsyncMock())

    async with session_factory() as session:
        created = await create_gasto(session, _payload())
        listing = await list_by_month(session, TEST_YEAR, TEST_MONTH)

    assert created.concepto == "Celulares"
    assert created.monto == Decimal("150000.00")
    assert len(listing.gastos) == 1
    assert listing.total == Decimal("150000.00")


@pytest.mark.asyncio
async def test_list_excluye_otros_meses(
    session_factory: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("services.gasto_extraordinario_service.publish", AsyncMock())

    async with session_factory() as session:
        await create_gasto(session, _payload(fecha=date(TEST_YEAR, TEST_MONTH, 10)))
        await create_gasto(session, _payload(fecha=date(TEST_YEAR, 8, 10), concepto="Papeles"))
        julio = await list_by_month(session, TEST_YEAR, TEST_MONTH)
        agosto = await list_by_month(session, TEST_YEAR, 8)

    assert len(julio.gastos) == 1
    assert len(agosto.gastos) == 1
    assert agosto.gastos[0].concepto == "Papeles"


@pytest.mark.asyncio
async def test_update_gasto(
    session_factory: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("services.gasto_extraordinario_service.publish", AsyncMock())

    async with session_factory() as session:
        created = await create_gasto(session, _payload())
        updated = await update_gasto(
            session,
            created.id,
            GastoExtraordinarioUpdate(monto=Decimal("200000.00")),
        )

    assert updated.monto == Decimal("200000.00")


@pytest.mark.asyncio
async def test_delete_gasto(
    session_factory: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("services.gasto_extraordinario_service.publish", AsyncMock())

    async with session_factory() as session:
        created = await create_gasto(session, _payload())
        await delete_gasto(session, created.id)
        listing = await list_by_month(session, TEST_YEAR, TEST_MONTH)

    assert listing.gastos == []
    assert listing.total == Decimal("0.00")


@pytest.mark.asyncio
async def test_delete_not_found(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        with pytest.raises(GastoExtraordinarioNotFoundError):
            await delete_gasto(session, uuid.uuid4())

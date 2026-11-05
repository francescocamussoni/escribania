"""TDD unit tests for pago_colegio_bulk_service (WU-018)."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from models.escritura import EstadoEscritura
from models.pago_colegio import TipoPagoEscribania
from schemas.pago_colegio_bulk import PagoColegioBulkPreviewRequest, PagoColegioBulkRequest
from services.escritura_errors import EscrituraNotFoundError
from services.pago_colegio_bulk_service import (
    PagoColegioBulkValidationError,
    confirm_bulk,
    preview_bulk,
)
from helpers.escritura_factory import insert_test_escritura, insert_test_pago_colegio

TEST_DATE = date(2026, 7, 20)
CANONICAL_TOTAL_IMPUESTOS = Decimal("5311489.50")


def _dt() -> datetime:
    return datetime(2026, 7, 10, 12, 0, 0, tzinfo=UTC)


class TestPagoColegioBulkSchemas:
    def test_preview_request_rejects_duplicate_ids(self) -> None:
        escritura_id = uuid4()
        with pytest.raises(ValidationError):
            PagoColegioBulkPreviewRequest.model_validate(
                {"escritura_ids": [str(escritura_id), str(escritura_id)]}
            )

    def test_confirm_request_rejects_duplicate_escritura_ids(self) -> None:
        escritura_id = uuid4()
        with pytest.raises(ValidationError):
            PagoColegioBulkRequest.model_validate(
                {
                    "fecha": "2026-07-20",
                    "items": [
                        {"escritura_id": str(escritura_id), "monto": "100.00"},
                        {"escritura_id": str(escritura_id), "monto": "200.00"},
                    ],
                }
            )


@pytest.mark.asyncio
async def test_preview_pendiente_desde_total_impuestos_efectivo_menos_pagos_colegio(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session, seeded_config, created_at=_dt(), estado=EstadoEscritura.ABIERTA
        )
        await insert_test_pago_colegio(
            session,
            escritura.id,
            monto=Decimal("1000000.00"),
            fecha=TEST_DATE,
            tipo=TipoPagoEscribania.COLEGIO,
        )
        await insert_test_pago_colegio(
            session,
            escritura.id,
            monto=Decimal("500000.00"),
            fecha=TEST_DATE,
            tipo=TipoPagoEscribania.OTROS,
            concepto="Gasto misc",
        )

        preview = await preview_bulk(
            session,
            PagoColegioBulkPreviewRequest(escritura_ids=[escritura.id]),
        )

        assert len(preview.items) == 1
        item = preview.items[0]
        assert item.elegible is True
        assert item.motivo is None
        assert item.pendiente == CANONICAL_TOTAL_IMPUESTOS - Decimal("1000000.00")
        assert preview.total_propuesto == item.pendiente


@pytest.mark.asyncio
async def test_preview_excluye_escritura_cerrada(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
) -> None:
    async with session_factory() as session:
        cerrada = await insert_test_escritura(
            session,
            seeded_config,
            created_at=_dt(),
            estado=EstadoEscritura.CERRADA,
            nombre="Cerrada bulk",
        )

        preview = await preview_bulk(
            session,
            PagoColegioBulkPreviewRequest(escritura_ids=[cerrada.id]),
        )

        assert preview.items[0].elegible is False
        assert preview.items[0].motivo == "cerrada"
        assert preview.total_propuesto == Decimal("0.00")


@pytest.mark.asyncio
async def test_preview_sin_pendiente_no_elegible(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session, seeded_config, created_at=_dt(), estado=EstadoEscritura.ABIERTA
        )
        await insert_test_pago_colegio(
            session,
            escritura.id,
            monto=CANONICAL_TOTAL_IMPUESTOS,
            fecha=TEST_DATE,
            tipo=TipoPagoEscribania.COLEGIO,
        )

        preview = await preview_bulk(
            session,
            PagoColegioBulkPreviewRequest(escritura_ids=[escritura.id]),
        )

        assert preview.items[0].elegible is False
        assert preview.items[0].motivo == "sin_pendiente"
        assert preview.items[0].pendiente == Decimal("0.00")
        assert preview.total_propuesto == Decimal("0.00")


@pytest.mark.asyncio
async def test_preview_unknown_escritura_raises_not_found(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        with pytest.raises(EscrituraNotFoundError):
            await preview_bulk(
                session,
                PagoColegioBulkPreviewRequest(escritura_ids=[uuid4()]),
            )


@pytest.mark.asyncio
async def test_confirm_crea_pagos_colegio_misma_fecha(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
) -> None:
    async with session_factory() as session:
        escritura_a = await insert_test_escritura(
            session,
            seeded_config,
            created_at=_dt(),
            nombre="Bulk A",
        )
        escritura_b = await insert_test_escritura(
            session,
            seeded_config,
            created_at=_dt(),
            nombre="Bulk B",
        )
        fecha = date(2026, 7, 25)
        monto_a = Decimal("1000.00")
        monto_b = Decimal("2500.50")

        result = await confirm_bulk(
            session,
            PagoColegioBulkRequest(
                fecha=fecha,
                items=[
                    {"escritura_id": escritura_a.id, "monto": monto_a},
                    {"escritura_id": escritura_b.id, "monto": monto_b},
                ],
            ),
        )

        assert len(result.pagos) == 2
        assert result.total == Decimal("3500.50")
        for pago in result.pagos:
            assert pago.tipo == TipoPagoEscribania.COLEGIO
            assert pago.fecha == fecha


@pytest.mark.asyncio
async def test_confirm_rechaza_items_no_elegibles(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
) -> None:
    async with session_factory() as session:
        cerrada = await insert_test_escritura(
            session,
            seeded_config,
            created_at=_dt(),
            estado=EstadoEscritura.CERRADA,
            nombre="Cerrada confirm",
        )

        with pytest.raises(PagoColegioBulkValidationError):
            await confirm_bulk(
                session,
                PagoColegioBulkRequest(
                    fecha=TEST_DATE,
                    items=[{"escritura_id": cerrada.id, "monto": Decimal("100.00")}],
                ),
            )


@pytest.mark.asyncio
async def test_confirm_permite_monto_editable_por_escritura(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session, seeded_config, created_at=_dt(), nombre="Editable monto"
        )
        monto_parcial = Decimal("12345.67")

        result = await confirm_bulk(
            session,
            PagoColegioBulkRequest(
                fecha=TEST_DATE,
                items=[{"escritura_id": escritura.id, "monto": monto_parcial}],
            ),
        )

        assert result.pagos[0].monto == monto_parcial
        assert result.total == monto_parcial

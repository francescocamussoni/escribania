"""TDD unit tests for impuesto_service (WU-013 — FAIL FIRST until WU-014)."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from models.escritura import EstadoEscritura
from models.impuesto_escritura import DireccionProrrateo, ImpuestoEscritura, TipoImpuesto
from models.pago_impuesto_cliente import PagoImpuestoCliente
from models.pago_impuesto_escribania import PagoImpuestoEscribania
from schemas.impuesto import ImpuestoInput, ImpuestoUpdate
from services.escritura_errors import EscrituraClosedError
from services.impuesto_service import (
    ImpuestoConPagosError,
    ImpuestoNotFoundError,
    create_impuesto,
    delete_impuesto,
    list_impuestos,
    update_impuesto,
)
from helpers.escritura_factory import insert_test_escritura

MONTO_TOTAL = Decimal("10000.00")
PERIODO_INICIO = date(2026, 5, 1)
PERIODO_FIN = date(2026, 6, 30)
FECHA_CORTE = date(2026, 6, 15)
MONTO_SUGERIDO_ATRAS = Decimal("7540.98")
MONTO_SUGERIDO_ADELANTE = Decimal("2459.02")


def _dt() -> datetime:
    return datetime(2026, 7, 10, 12, 0, 0, tzinfo=UTC)


def _canonical_input(
    *,
    direccion: DireccionProrrateo = DireccionProrrateo.HACIA_ATRAS,
    tipo: TipoImpuesto = TipoImpuesto.API,
) -> ImpuestoInput:
    return ImpuestoInput(
        tipo=tipo,
        monto_total=MONTO_TOTAL,
        periodo_inicio=PERIODO_INICIO,
        periodo_fin=PERIODO_FIN,
        fecha_corte=FECHA_CORTE,
        direccion_prorrateo=direccion,
    )


class TestImpuestoSchema:
    def test_input_accepts_valid_payload(self) -> None:
        payload = ImpuestoInput.model_validate({
            "tipo": "API",
            "monto_total": "10000.00",
            "periodo_inicio": "2026-05-01",
            "periodo_fin": "2026-06-30",
            "fecha_corte": "2026-06-15",
            "direccion_prorrateo": "hacia_atras",
        })
        assert payload.monto_total == MONTO_TOTAL
        assert payload.tipo == TipoImpuesto.API

    def test_input_accepts_all_tipo_impuesto_enum_values(self) -> None:
        for tipo in TipoImpuesto:
            payload = ImpuestoInput.model_validate({
                "tipo": tipo.value,
                "monto_total": "100.00",
                "periodo_inicio": "2026-05-01",
                "periodo_fin": "2026-06-30",
                "fecha_corte": "2026-06-15",
                "direccion_prorrateo": "hacia_atras",
            })
            assert payload.tipo == tipo

    def test_input_rejects_periodo_invalido(self) -> None:
        with pytest.raises(ValidationError):
            ImpuestoInput.model_validate({
                "tipo": "API",
                "monto_total": "10000.00",
                "periodo_inicio": "2026-06-30",
                "periodo_fin": "2026-05-01",
                "fecha_corte": "2026-06-15",
                "direccion_prorrateo": "hacia_atras",
            })

    def test_input_rejects_monto_cero(self) -> None:
        with pytest.raises(ValidationError):
            ImpuestoInput.model_validate({
                "tipo": "API",
                "monto_total": "0",
                "periodo_inicio": "2026-05-01",
                "periodo_fin": "2026-06-30",
                "fecha_corte": "2026-06-15",
                "direccion_prorrateo": "hacia_atras",
            })

    def test_input_rejects_monto_negativo(self) -> None:
        with pytest.raises(ValidationError):
            ImpuestoInput.model_validate({
                "tipo": "API",
                "monto_total": "-1.00",
                "periodo_inicio": "2026-05-01",
                "periodo_fin": "2026-06-30",
                "fecha_corte": "2026-06-15",
                "direccion_prorrateo": "hacia_atras",
            })

    def test_input_rejects_fecha_corte_fuera_de_periodo(self) -> None:
        with pytest.raises(ValidationError):
            ImpuestoInput.model_validate({
                "tipo": "API",
                "monto_total": "10000.00",
                "periodo_inicio": "2026-05-01",
                "periodo_fin": "2026-06-30",
                "fecha_corte": "2026-07-01",
                "direccion_prorrateo": "hacia_atras",
            })

    def test_input_rejects_extra_fields(self) -> None:
        with pytest.raises(ValidationError):
            ImpuestoInput.model_validate({
                "tipo": "API",
                "monto_total": "10000.00",
                "periodo_inicio": "2026-05-01",
                "periodo_fin": "2026-06-30",
                "fecha_corte": "2026-06-15",
                "direccion_prorrateo": "hacia_atras",
                "unknown": "x",
            })

    def test_update_rejects_empty_payload(self) -> None:
        with pytest.raises(ValidationError):
            ImpuestoUpdate.model_validate({})


@pytest.mark.asyncio
async def test_create_impuesto_valido_retorna_monto_prorrateado_sugerido(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session, seeded_config, created_at=_dt(), estado=EstadoEscritura.ABIERTA
        )

        response = await create_impuesto(session, escritura.id, _canonical_input())

        assert response.escritura_id == escritura.id
        assert response.tipo == TipoImpuesto.API
        assert response.monto_total == MONTO_TOTAL
        assert response.monto_prorrateado_sugerido == MONTO_SUGERIDO_ATRAS
        assert response.estado_pagos == "sin_pagos"
        assert response.pago_cliente is None
        assert response.pago_escribania is None


@pytest.mark.asyncio
async def test_create_impuesto_hacia_adelante_calcula_sugerido_15_61(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session, seeded_config, created_at=_dt(), estado=EstadoEscritura.ABIERTA
        )

        response = await create_impuesto(
            session,
            escritura.id,
            _canonical_input(direccion=DireccionProrrateo.HACIA_ADELANTE),
        )

        assert response.monto_prorrateado_sugerido == MONTO_SUGERIDO_ADELANTE


@pytest.mark.asyncio
async def test_create_impuesto_rechaza_escritura_cerrada(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session, seeded_config, created_at=_dt(), estado=EstadoEscritura.CERRADA
        )

        with pytest.raises(EscrituraClosedError):
            await create_impuesto(session, escritura.id, _canonical_input())


@pytest.mark.asyncio
async def test_update_impuesto_recalcula_monto_prorrateado_sugerido(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session, seeded_config, created_at=_dt(), estado=EstadoEscritura.ABIERTA
        )
        created = await create_impuesto(session, escritura.id, _canonical_input())
        assert created.monto_prorrateado_sugerido == MONTO_SUGERIDO_ATRAS

        updated = await update_impuesto(
            session,
            escritura.id,
            created.id,
            ImpuestoUpdate(direccion_prorrateo=DireccionProrrateo.HACIA_ADELANTE),
        )

        assert updated.monto_prorrateado_sugerido == MONTO_SUGERIDO_ADELANTE


@pytest.mark.asyncio
async def test_update_impuesto_rechaza_escritura_cerrada(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session, seeded_config, created_at=_dt(), estado=EstadoEscritura.ABIERTA
        )
        created = await create_impuesto(session, escritura.id, _canonical_input())
        escritura.estado = EstadoEscritura.CERRADA
        await session.commit()

        with pytest.raises(EscrituraClosedError):
            await update_impuesto(
                session,
                escritura.id,
                created.id,
                ImpuestoUpdate(monto_total=Decimal("12000.00")),
            )


@pytest.mark.asyncio
async def test_delete_impuesto_sin_pagos_ok(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session, seeded_config, created_at=_dt(), estado=EstadoEscritura.ABIERTA
        )
        created = await create_impuesto(session, escritura.id, _canonical_input())

        await delete_impuesto(session, escritura.id, created.id)

        listing = await list_impuestos(session, escritura.id)
        assert listing.impuestos == []


@pytest.mark.asyncio
async def test_delete_impuesto_con_pagos_rechazado(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session, seeded_config, created_at=_dt(), estado=EstadoEscritura.ABIERTA
        )
        created = await create_impuesto(session, escritura.id, _canonical_input())
        impuesto = await session.get(ImpuestoEscritura, created.id)
        assert impuesto is not None
        session.add(
            PagoImpuestoCliente(
                id=uuid.uuid4(),
                impuesto_id=impuesto.id,
                escritura_id=escritura.id,
                monto=MONTO_SUGERIDO_ATRAS,
                fecha=date(2026, 7, 1),
            )
        )
        await session.commit()

        with pytest.raises(ImpuestoConPagosError):
            await delete_impuesto(session, escritura.id, created.id)


@pytest.mark.asyncio
async def test_delete_impuesto_not_found(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session, seeded_config, created_at=_dt(), estado=EstadoEscritura.ABIERTA
        )

        with pytest.raises(ImpuestoNotFoundError):
            await delete_impuesto(session, escritura.id, uuid.uuid4())


@pytest.mark.asyncio
async def test_list_impuestos_incluye_balance_agregado(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session, seeded_config, created_at=_dt(), estado=EstadoEscritura.ABIERTA
        )
        first = await create_impuesto(session, escritura.id, _canonical_input())
        second = await create_impuesto(
            session,
            escritura.id,
            _canonical_input(tipo=TipoImpuesto.TGI),
        )

        listing = await list_impuestos(session, escritura.id)

        assert len(listing.impuestos) == 2
        assert {item.id for item in listing.impuestos} == {first.id, second.id}
        assert listing.balance.total_cliente == Decimal("0.00")
        assert listing.balance.total_escribania == Decimal("0.00")
        assert listing.balance.balance == Decimal("0.00")
        assert listing.balance.puede_cerrar is False
        assert len(listing.balance.impuestos_pendientes) == 2


@pytest.mark.asyncio
async def test_list_impuestos_deriva_estado_pagos(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_config,
) -> None:
    async with session_factory() as session:
        escritura = await insert_test_escritura(
            session, seeded_config, created_at=_dt(), estado=EstadoEscritura.ABIERTA
        )
        sin_pagos = await create_impuesto(session, escritura.id, _canonical_input())
        solo_cliente = await create_impuesto(
            session,
            escritura.id,
            _canonical_input(tipo=TipoImpuesto.TGI),
        )
        solo_escribania = await create_impuesto(
            session,
            escritura.id,
            _canonical_input(tipo=TipoImpuesto.EPE),
        )
        completos = await create_impuesto(
            session,
            escritura.id,
            _canonical_input(tipo=TipoImpuesto.EXPENSAS),
        )

        for impuesto_id, monto in (
            (solo_cliente.id, MONTO_SUGERIDO_ATRAS),
            (completos.id, MONTO_SUGERIDO_ATRAS),
        ):
            session.add(
                PagoImpuestoCliente(
                    id=uuid.uuid4(),
                    impuesto_id=impuesto_id,
                    escritura_id=escritura.id,
                    monto=monto,
                    fecha=date(2026, 7, 1),
                )
            )

        for impuesto_id, monto in (
            (solo_escribania.id, MONTO_SUGERIDO_ADELANTE),
            (completos.id, MONTO_SUGERIDO_ADELANTE),
        ):
            session.add(
                PagoImpuestoEscribania(
                    id=uuid.uuid4(),
                    impuesto_id=impuesto_id,
                    escritura_id=escritura.id,
                    monto=monto,
                    fecha=date(2026, 7, 2),
                )
            )
        await session.commit()

        listing = await list_impuestos(session, escritura.id)
        by_id = {item.id: item for item in listing.impuestos}

        assert by_id[sin_pagos.id].estado_pagos == "sin_pagos"
        assert by_id[solo_cliente.id].estado_pagos == "solo_cliente"
        assert by_id[solo_escribania.id].estado_pagos == "solo_escribania"
        assert by_id[completos.id].estado_pagos == "completos"

        assert listing.balance.total_cliente == MONTO_SUGERIDO_ATRAS * 2
        assert listing.balance.total_escribania == MONTO_SUGERIDO_ADELANTE * 2
        assert listing.balance.balance == MONTO_SUGERIDO_ATRAS * 2 - MONTO_SUGERIDO_ADELANTE * 2
        assert listing.balance.puede_cerrar is False
        assert len(listing.balance.impuestos_pendientes) == 3

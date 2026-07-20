"""Integration tests for Alembic migration 006_pagos_cliente."""

from __future__ import annotations

import subprocess
import uuid
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from models.configuracion import ConfiguracionFinanciera
from models.escritura import EstadoEscritura

IMPLICIT_PAYMENT_CONCEPT = "Migración: pago implícito al cierre"
REVISION_006 = "006"
REVISION_005 = "005"
BACKEND_ROOT = Path(__file__).resolve().parents[2]


def _run_alembic(action: str, revision: str) -> None:
    """Run alembic in a subprocess to avoid asyncio event-loop conflicts."""
    result = subprocess.run(
        ["uv", "run", "alembic", action, revision],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"alembic {action} {revision} failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )


async def _table_names(engine: AsyncEngine) -> set[str]:
    async with engine.connect() as conn:

        def _inspect(sync_conn) -> set[str]:
            return set(inspect(sync_conn).get_table_names())

        return await conn.run_sync(_inspect)


@pytest.mark.asyncio
async def test_migration_006_schema(db_engine: AsyncEngine) -> None:
    """pagos_* tables exist; gastos_adicionales was removed."""
    tables = await _table_names(db_engine)
    assert "pagos_cliente" in tables
    assert "pagos_colegio" in tables
    assert "gastos_adicionales" not in tables


@pytest.mark.asyncio
async def test_migration_006_indexes_and_constraints(db_engine: AsyncEngine) -> None:
    async with db_engine.connect() as conn:

        def _inspect(sync_conn) -> None:
            inspector = inspect(sync_conn)
            for table in ("pagos_cliente", "pagos_colegio"):
                index_names = {idx["name"] for idx in inspector.get_indexes(table)}
                assert f"ix_{table}_escritura_id" in index_names
                assert f"ix_{table}_fecha" in index_names

                check_names = {chk["name"] for chk in inspector.get_check_constraints(table)}
                assert f"ck_{table}_monto_positive" in check_names

        await conn.run_sync(_inspect)


@pytest.mark.asyncio
async def test_migration_006_closed_escrituras_have_pago_cliente(db_engine: AsyncEngine) -> None:
    """Every closed escritura must have at least one pagos_cliente row (FR-035)."""
    async with db_engine.connect() as conn:
        result = await conn.execute(
            text(
                """
                SELECT COUNT(*) AS missing
                FROM escrituras e
                WHERE e.estado = 'cerrada'
                  AND NOT EXISTS (
                      SELECT 1 FROM pagos_cliente pc WHERE pc.escritura_id = e.id
                  )
                """
            )
        )
        missing = result.scalar_one()
        assert missing == 0


@pytest.mark.asyncio
async def test_migration_006_data_migration_roundtrip(db_engine: AsyncEngine) -> None:
    """Downgrade to 005, seed gastos + closed escritura, upgrade — verify migrated data."""
    from sqlalchemy import select

    from tests.helpers.escritura_factory import insert_test_escritura

    _run_alembic("downgrade", REVISION_005)

    try:
        async with AsyncSession(db_engine, expire_on_commit=False) as session:
            config_row = await session.scalar(
                select(ConfiguracionFinanciera).order_by(ConfiguracionFinanciera.version.desc()).limit(1)
            )
            assert config_row is not None, "configuracion_financiera required for migration test"

            escriba_abierta = await insert_test_escritura(
                session,
                config_row,
                nombre="Migración abierta",
                created_at=datetime(2026, 1, 10, tzinfo=UTC),
                estado=EstadoEscritura.ABIERTA,
            )
            escriba_cerrada = await insert_test_escritura(
                session,
                config_row,
                nombre="Migración cerrada",
                created_at=datetime(2026, 1, 5, tzinfo=UTC),
                estado=EstadoEscritura.CERRADA,
            )

            gasto_entrada_id = uuid.uuid4()
            gasto_salida_id = uuid.uuid4()
            await session.execute(
                text(
                    """
                    INSERT INTO gastos_adicionales
                        (id, escritura_id, concepto, monto, direccion, fecha)
                    VALUES
                        (:entrada_id, :escritura_id, 'Anticipo cliente', 50000.00, 'entrada', :fecha),
                        (:salida_id, :escritura_id, 'Tasa colegio', 12000.00, 'salida', :fecha)
                    """
                ),
                {
                    "entrada_id": gasto_entrada_id,
                    "salida_id": gasto_salida_id,
                    "escritura_id": escriba_abierta.id,
                    "fecha": date(2026, 1, 15),
                },
            )
            await session.commit()

            abierta_id = escriba_abierta.id
            cerrada_id = escriba_cerrada.id

        _run_alembic("upgrade", REVISION_006)

        tables = await _table_names(db_engine)
        assert "gastos_adicionales" not in tables

        async with db_engine.connect() as conn:
            cliente_rows = (
                await conn.execute(
                    text("SELECT id, concepto FROM pagos_cliente WHERE escritura_id = :id"),
                    {"id": abierta_id},
                )
            ).all()
            assert len(cliente_rows) == 1
            assert cliente_rows[0].id == gasto_entrada_id
            assert cliente_rows[0].concepto == "Anticipo cliente"

            colegio_rows = (
                await conn.execute(
                    text("SELECT id, concepto FROM pagos_colegio WHERE escritura_id = :id"),
                    {"id": abierta_id},
                )
            ).all()
            assert len(colegio_rows) == 1
            assert colegio_rows[0].id == gasto_salida_id

            implicit = (
                await conn.execute(
                    text(
                        """
                        SELECT concepto, monto
                        FROM pagos_cliente
                        WHERE escritura_id = :id
                        """
                    ),
                    {"id": cerrada_id},
                )
            ).one()
            assert implicit.concepto == IMPLICIT_PAYMENT_CONCEPT
            assert implicit.monto > 0

    finally:
        _run_alembic("upgrade", REVISION_006)


@pytest.mark.asyncio
async def test_migration_006_upgrade_head_idempotent(db_engine: AsyncEngine) -> None:
    """Running upgrade head twice must succeed without error."""
    _run_alembic("upgrade", "head")
    _run_alembic("upgrade", "head")
    tables = await _table_names(db_engine)
    assert "pagos_cliente" in tables

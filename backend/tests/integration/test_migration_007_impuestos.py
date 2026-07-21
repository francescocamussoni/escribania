"""Integration tests for Alembic migration 007_impuestos_escritura."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncEngine

REVISION_007 = "007"
REVISION_006 = "006"
BACKEND_ROOT = Path(__file__).resolve().parents[2]

_IMPUESTO_TABLES = (
    "impuestos_escritura",
    "pagos_impuesto_cliente",
    "pagos_impuesto_escribania",
)

_TIPO_IMPUESTO_VALUES = {
    "API",
    "TGI",
    "AGUAS_SANTAFESINAS",
    "EPE",
    "EXPENSAS",
    "LITORAL_GAS",
}

_DIRECCION_PRORRATEO_VALUES = {"hacia_atras", "hacia_adelante"}


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


@pytest.fixture(scope="module", autouse=True)
def ensure_migration_007_at_head() -> None:
    """Apply migration 007 before schema inspection tests (same pattern as CI migrate)."""
    _run_alembic("upgrade", "head")


async def _table_names(engine: AsyncEngine) -> set[str]:
    async with engine.connect() as conn:

        def _inspect(sync_conn) -> set[str]:
            return set(inspect(sync_conn).get_table_names())

        return await conn.run_sync(_inspect)


@pytest.mark.asyncio
async def test_migration_007_schema(db_engine: AsyncEngine) -> None:
    """impuestos_* tables exist after upgrade to head."""
    tables = await _table_names(db_engine)
    for table in _IMPUESTO_TABLES:
        assert table in tables


@pytest.mark.asyncio
async def test_migration_007_enums(db_engine: AsyncEngine) -> None:
    async with db_engine.connect() as conn:
        tipo_rows = (
            await conn.execute(
                text(
                    """
                    SELECT e.enumlabel
                    FROM pg_type t
                    JOIN pg_enum e ON t.oid = e.enumtypid
                    WHERE t.typname = 'tipo_impuesto'
                    ORDER BY e.enumsortorder
                    """
                )
            )
        ).all()
        direccion_rows = (
            await conn.execute(
                text(
                    """
                    SELECT e.enumlabel
                    FROM pg_type t
                    JOIN pg_enum e ON t.oid = e.enumtypid
                    WHERE t.typname = 'direccion_prorrateo'
                    ORDER BY e.enumsortorder
                    """
                )
            )
        ).all()

    assert {row.enumlabel for row in tipo_rows} == _TIPO_IMPUESTO_VALUES
    assert {row.enumlabel for row in direccion_rows} == _DIRECCION_PRORRATEO_VALUES


@pytest.mark.asyncio
async def test_migration_007_indexes_and_constraints(db_engine: AsyncEngine) -> None:
    async with db_engine.connect() as conn:

        def _inspect(sync_conn) -> None:
            inspector = inspect(sync_conn)

            impuesto_indexes = {idx["name"] for idx in inspector.get_indexes("impuestos_escritura")}
            assert "ix_impuestos_escritura_escritura_id" in impuesto_indexes
            assert "ix_impuestos_escritura_tipo_periodo" in impuesto_indexes

            impuesto_checks = {
                chk["name"] for chk in inspector.get_check_constraints("impuestos_escritura")
            }
            assert "ck_impuestos_escritura_monto_positive" in impuesto_checks
            assert "ck_impuestos_escritura_periodo_valido" in impuesto_checks

            impuesto_fks = inspector.get_foreign_keys("impuestos_escritura")
            assert any(
                fk["referred_table"] == "escrituras" and "escritura_id" in fk["constrained_columns"]
                for fk in impuesto_fks
            )

            for table in ("pagos_impuesto_cliente", "pagos_impuesto_escribania"):
                index_names = {idx["name"] for idx in inspector.get_indexes(table)}
                assert f"ix_{table}_escritura_id" in index_names
                assert f"ix_{table}_fecha" in index_names

                check_names = {chk["name"] for chk in inspector.get_check_constraints(table)}
                assert f"ck_{table}_monto_positive" in check_names

                unique_names = {
                    uc["name"] for uc in inspector.get_unique_constraints(table)
                }
                assert f"uq_{table}_impuesto_id" in unique_names

        await conn.run_sync(_inspect)


@pytest.mark.asyncio
async def test_migration_007_upgrade_head_idempotent(db_engine: AsyncEngine) -> None:
    """Running upgrade head twice must succeed without error."""
    _run_alembic("upgrade", "head")
    _run_alembic("upgrade", "head")
    tables = await _table_names(db_engine)
    for table in _IMPUESTO_TABLES:
        assert table in tables


@pytest.mark.asyncio
async def test_migration_007_downgrade_roundtrip(db_engine: AsyncEngine) -> None:
    """Downgrade to 006 removes impuestos schema; upgrade restores it."""
    _run_alembic("downgrade", REVISION_006)

    try:
        tables = await _table_names(db_engine)
        for table in _IMPUESTO_TABLES:
            assert table not in tables

        async with db_engine.connect() as conn:
            enum_count = (
                await conn.execute(
                    text(
                        """
                        SELECT COUNT(*) AS n
                        FROM pg_type
                        WHERE typname IN ('tipo_impuesto', 'direccion_prorrateo')
                        """
                    )
                )
            ).scalar_one()
            assert enum_count == 0

        _run_alembic("upgrade", REVISION_007)
        tables_after = await _table_names(db_engine)
        for table in _IMPUESTO_TABLES:
            assert table in tables_after

    finally:
        _run_alembic("upgrade", "head")

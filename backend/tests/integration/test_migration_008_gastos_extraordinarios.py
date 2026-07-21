"""Integration tests for Alembic migration 008_gastos_extraordinarios."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncEngine

REVISION_008 = "008"
REVISION_007 = "007"
BACKEND_ROOT = Path(__file__).resolve().parents[2]

_TABLE = "gastos_extraordinarios"


def _run_alembic(action: str, revision: str) -> None:
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
def ensure_migration_008_at_head() -> None:
    _run_alembic("upgrade", "head")


async def _table_names(engine: AsyncEngine) -> set[str]:
    async with engine.connect() as conn:

        def _inspect(sync_conn) -> set[str]:
            return set(inspect(sync_conn).get_table_names())

        return await conn.run_sync(_inspect)


@pytest.mark.asyncio
async def test_migration_008_schema(db_engine: AsyncEngine) -> None:
    tables = await _table_names(db_engine)
    assert _TABLE in tables


@pytest.mark.asyncio
async def test_migration_008_indexes_and_constraints(db_engine: AsyncEngine) -> None:
    async with db_engine.connect() as conn:

        def _inspect(sync_conn) -> None:
            inspector = inspect(sync_conn)
            index_names = {idx["name"] for idx in inspector.get_indexes(_TABLE)}
            assert "ix_gastos_extraordinarios_fecha" in index_names

            check_names = {chk["name"] for chk in inspector.get_check_constraints(_TABLE)}
            assert "ck_gastos_extraordinarios_monto_positive" in check_names
            assert "ck_gastos_extraordinarios_concepto_not_empty" in check_names

            columns = {col["name"] for col in inspector.get_columns(_TABLE)}
            assert {"id", "concepto", "monto", "fecha", "created_at", "updated_at"} <= columns

        await conn.run_sync(_inspect)


@pytest.mark.asyncio
async def test_migration_008_upgrade_head_idempotent(db_engine: AsyncEngine) -> None:
    _run_alembic("upgrade", "head")
    _run_alembic("upgrade", "head")
    tables = await _table_names(db_engine)
    assert _TABLE in tables


@pytest.mark.asyncio
async def test_migration_008_downgrade_roundtrip(db_engine: AsyncEngine) -> None:
    _run_alembic("downgrade", REVISION_007)

    try:
        tables = await _table_names(db_engine)
        assert _TABLE not in tables

        _run_alembic("upgrade", REVISION_008)
        tables_after = await _table_names(db_engine)
        assert _TABLE in tables_after

    finally:
        _run_alembic("upgrade", "head")

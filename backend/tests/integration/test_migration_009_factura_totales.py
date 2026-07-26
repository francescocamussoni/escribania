"""Integration tests for Alembic migration 009_factura_totales."""

from __future__ import annotations

import subprocess
from decimal import Decimal
from pathlib import Path

import pytest
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncEngine

REVISION_009 = "009"
BACKEND_ROOT = Path(__file__).resolve().parents[2]

_TABLE = "facturas_principales"
_NEW_COLUMNS = ("dif_honorarios", "total_parcial", "total_sin_iva", "iva")


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
def ensure_migration_009_at_head() -> None:
    _run_alembic("upgrade", "head")


@pytest.mark.asyncio
async def test_migration_009_columns_not_null(db_engine: AsyncEngine) -> None:
    async with db_engine.connect() as conn:

        def _inspect(sync_conn) -> None:
            inspector = inspect(sync_conn)
            columns = {col["name"]: col for col in inspector.get_columns(_TABLE)}
            for name in _NEW_COLUMNS:
                assert name in columns
                assert columns[name]["nullable"] is False

        await conn.run_sync(_inspect)


@pytest.mark.asyncio
async def test_migration_009_backfill_coherent(db_engine: AsyncEngine) -> None:
    async with db_engine.connect() as conn:
        row = (
            await conn.execute(
                sa.text(
                    f"""
                    SELECT dif_honorarios, total_parcial, total_sin_iva, iva, total_factura
                    FROM {_TABLE}
                    LIMIT 1
                    """
                )
            )
        ).mappings().first()

    if row is None:
        pytest.skip("No facturas_principales rows to validate backfill")

    dif = Decimal(str(row["dif_honorarios"]))
    total_sin_iva = Decimal(str(row["total_sin_iva"]))
    iva = Decimal(str(row["iva"]))
    total_factura = Decimal(str(row["total_factura"]))
    assert total_factura == total_sin_iva + iva
    assert dif >= Decimal("0")

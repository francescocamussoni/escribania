"""Unit tests for SoftDeleteMixin — TDD: written FAILING before implementation.

Tests verify:
- Rows with deleted_at populated are excluded from standard ORM queries.
- execution_options(include_deleted=True) bypasses the filter and includes them.
- soft_delete() method sets deleted_at to a non-null datetime.
- Filtering on a class without SoftDeleteMixin is unaffected.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
import pytest_asyncio
from sqlalchemy import Index, String, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import DateTime, func

from models.mixins import SoftDeleteMixin


# ---------------------------------------------------------------------------
# Minimal in-test Base — uses real Postgres so the partial index and
# do_orm_execute hook work exactly as in production.
# ---------------------------------------------------------------------------

class TestBase(DeclarativeBase):
    pass


class SoftDeletableEntity(SoftDeleteMixin, TestBase):
    """Minimal entity that uses SoftDeleteMixin for filter tests."""

    __tablename__ = "test_soft_delete_entity"
    __table_args__ = (
        Index("ix_test_sde_deleted_at", "deleted_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def soft_delete_engine(db_engine: AsyncEngine) -> AsyncEngine:
    """Reuse the real test engine; create the test table then tear it down."""
    async with db_engine.begin() as conn:
        await conn.run_sync(TestBase.metadata.create_all)
    yield db_engine
    async with db_engine.begin() as conn:
        await conn.run_sync(TestBase.metadata.drop_all)


@pytest_asyncio.fixture
async def soft_delete_session(soft_delete_engine: AsyncEngine) -> AsyncSession:
    factory = async_sessionmaker(soft_delete_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_soft_deleted_row_excluded_from_standard_query(soft_delete_session: AsyncSession) -> None:
    """Standard select() MUST NOT return rows where deleted_at is not null."""
    # Arrange
    active = SoftDeletableEntity(id=uuid.uuid4(), nombre="activo")
    deleted = SoftDeletableEntity(
        id=uuid.uuid4(),
        nombre="eliminado",
        deleted_at=datetime.now(UTC),
    )
    soft_delete_session.add_all([active, deleted])
    await soft_delete_session.commit()

    # Act — standard query without bypassing the filter
    result = await soft_delete_session.execute(select(SoftDeletableEntity))
    rows = result.scalars().all()
    nombres = {r.nombre for r in rows}

    # Assert
    assert "activo" in nombres, "Active row must appear in standard queries"
    assert "eliminado" not in nombres, "Soft-deleted row MUST be excluded from standard queries"  # BR001


@pytest.mark.asyncio
async def test_include_deleted_option_returns_soft_deleted_rows(soft_delete_session: AsyncSession) -> None:
    """execution_options(include_deleted=True) MUST bypass the soft-delete filter."""
    # Arrange
    deleted = SoftDeletableEntity(
        id=uuid.uuid4(),
        nombre="visible_con_flag",
        deleted_at=datetime.now(UTC),
    )
    soft_delete_session.add(deleted)
    await soft_delete_session.commit()

    # Act — bypassed query
    result = await soft_delete_session.execute(
        select(SoftDeletableEntity).execution_options(include_deleted=True)
    )
    rows = result.scalars().all()
    nombres = {r.nombre for r in rows}

    # Assert
    assert "visible_con_flag" in nombres, "include_deleted=True MUST expose soft-deleted rows"  # BR002


@pytest.mark.asyncio
async def test_soft_delete_method_sets_deleted_at(soft_delete_session: AsyncSession) -> None:
    """soft_delete() MUST set deleted_at to the current UTC datetime."""
    # Arrange — entity must have soft_delete() method once SoftDeleteMixin is applied
    entity = SoftDeletableEntity(id=uuid.uuid4(), nombre="para_eliminar")
    soft_delete_session.add(entity)
    await soft_delete_session.commit()
    await soft_delete_session.refresh(entity)

    assert entity.deleted_at is None, "Newly created entity must have deleted_at = None"

    # Act
    entity.soft_delete()
    await soft_delete_session.commit()
    await soft_delete_session.refresh(entity)

    # Assert
    assert entity.deleted_at is not None, "soft_delete() MUST set deleted_at"  # BR003
    assert entity.deleted_at.tzinfo is not None, "deleted_at MUST be timezone-aware"


@pytest.mark.asyncio
async def test_active_after_soft_delete_count_excludes_row(soft_delete_session: AsyncSession) -> None:
    """After soft_delete(), a count query on active rows MUST return one fewer."""
    # Arrange
    entity_a = SoftDeletableEntity(id=uuid.uuid4(), nombre="a")
    entity_b = SoftDeletableEntity(id=uuid.uuid4(), nombre="b")
    soft_delete_session.add_all([entity_a, entity_b])
    await soft_delete_session.commit()

    # count before
    result_before = await soft_delete_session.execute(select(SoftDeletableEntity))
    count_before = len(result_before.scalars().all())

    # Act
    entity_b.soft_delete()
    await soft_delete_session.commit()

    # count after
    result_after = await soft_delete_session.execute(select(SoftDeletableEntity))
    count_after = len(result_after.scalars().all())

    # Assert
    assert count_after == count_before - 1, "Soft-deleted row MUST be excluded from subsequent counts"  # BR001

"""Soft delete mixin for SQLAlchemy 2.0 ORM models.

Provides:
- `deleted_at` column (nullable TIMESTAMPTZ) — null = active, non-null = soft-deleted.
- `soft_delete()` method that stamps the current UTC datetime.
- Global `do_orm_execute` event listener (registered in `database.py`) that automatically
  appends `WHERE deleted_at IS NULL` to every ORM SELECT unless the query is executed with
  `execution_options(include_deleted=True)`.

Usage:
    class MyModel(SoftDeleteMixin, Base):
        ...

Bypass filter for admin queries:
    await session.execute(
        select(MyModel).execution_options(include_deleted=True)
    )
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column, with_loader_criteria


class SoftDeleteMixin:
    """Mixin that adds soft-delete capability to any SQLAlchemy mapped class.

    Must be listed BEFORE `Base` in the inheritance chain so that the
    `deleted_at` column descriptor is properly picked up by the ORM mapper.
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        index=True,
    )

    def soft_delete(self) -> None:
        """Mark this instance as deleted by stamping `deleted_at` with the current UTC time.

        Does NOT commit the session. The caller is responsible for committing.
        """  # BR003
        self.deleted_at = datetime.now(UTC)


def _apply_soft_delete_filter(execute_state: object) -> None:
    """SQLAlchemy 2.0 `do_orm_execute` event listener.

    Appends `WHERE deleted_at IS NULL` to every ORM SELECT query for models
    that include `SoftDeleteMixin`, unless `include_deleted=True` is passed
    as an execution option.

    Registered in `database.py` once at application startup via:
        event.listen(Session, "do_orm_execute", _apply_soft_delete_filter)
    """
    # Only intercept ORM SELECT statements; skip DML (insert/update/delete).
    if not execute_state.is_orm_statement:  # type: ignore[attr-defined]
        return
    if not execute_state.is_select:  # type: ignore[attr-defined]
        return
    if execute_state.execution_options.get("include_deleted", False):  # type: ignore[attr-defined]
        # BR002 — explicit bypass: include soft-deleted rows
        return

    execute_state.statement = execute_state.statement.options(  # type: ignore[attr-defined]
        with_loader_criteria(
            SoftDeleteMixin,
            lambda cls: cls.deleted_at.is_(None),  # BR001 — exclude deleted rows
            include_aliases=True,
        )
    )

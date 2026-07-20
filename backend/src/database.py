from collections.abc import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session

from config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def _register_soft_delete_listener() -> None:
    """Register the global soft-delete ORM execute listener.

    Imported lazily to avoid a circular import: `mixins` imports `Base` from
    this module; we call this function after `Base` is defined.
    """
    from models.mixins import _apply_soft_delete_filter  # noqa: PLC0415

    event.listen(Session, "do_orm_execute", _apply_soft_delete_filter)


_register_soft_delete_listener()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

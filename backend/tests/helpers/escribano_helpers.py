from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest_asyncio


@pytest_asyncio.fixture
async def cleanup_escribanos() -> AsyncGenerator[list[uuid.UUID], None]:
    """Collects IDs for test readability; teardown is handled by transactional rollback."""
    yield []

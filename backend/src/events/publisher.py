from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import asyncpg

from config import get_settings

logger = logging.getLogger(__name__)

CHANNEL = "escribania_events"


def _asyncpg_dsn() -> str:
    return get_settings().database_url.replace("postgresql+asyncpg://", "postgresql://")


class EventHub:
    """Broadcasts PostgreSQL NOTIFY messages to local SSE subscribers."""

    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[str]] = set()
        self._listener_conn: asyncpg.Connection | None = None
        self._started = False

    def subscribe(self) -> asyncio.Queue[str]:
        queue: asyncio.Queue[str] = asyncio.Queue(maxsize=100)
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[str]) -> None:
        self._subscribers.discard(queue)

    def _handle_notification(
        self,
        _connection: asyncpg.Connection,
        _pid: int,
        _channel: str,
        payload: str,
    ) -> None:
        for queue in list(self._subscribers):
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                logger.warning("SSE subscriber queue full; dropping event")

    async def start(self) -> None:
        if self._started:
            return
        self._listener_conn = await asyncpg.connect(_asyncpg_dsn())
        await self._listener_conn.add_listener(CHANNEL, self._handle_notification)
        self._started = True
        logger.info("EventHub listening on channel %s", CHANNEL)

    async def stop(self) -> None:
        if self._listener_conn is not None:
            await self._listener_conn.remove_listener(CHANNEL, self._handle_notification)
            await self._listener_conn.close()
            self._listener_conn = None
        self._started = False
        self._subscribers.clear()

    async def publish(self, event_type: str, data: dict[str, Any]) -> None:
        payload = json.dumps({"event": event_type, "data": data})
        conn = await asyncpg.connect(_asyncpg_dsn())
        try:
            await conn.execute("SELECT pg_notify($1, $2)", CHANNEL, payload)
        finally:
            await conn.close()


event_hub = EventHub()


async def publish(event_type: str, data: dict[str, Any]) -> None:
    await event_hub.publish(event_type, data)

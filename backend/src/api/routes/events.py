from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, Request
from starlette.responses import StreamingResponse

from api.deps import get_current_user
from events.publisher import event_hub
from models.usuario import Usuario

router = APIRouter(prefix="/events", tags=["events"])

HEARTBEAT_SECONDS = 30.0


async def _sse_stream(request: Request) -> AsyncGenerator[str, None]:
    queue = event_hub.subscribe()
    try:
        yield ": connected\n\n"
        while True:
            if await request.is_disconnected():
                break
            try:
                payload = await asyncio.wait_for(queue.get(), timeout=HEARTBEAT_SECONDS)
            except TimeoutError:
                yield ": heartbeat\n\n"
                continue

            message = json.loads(payload)
            event_type = message["event"]
            data = json.dumps(message["data"])
            yield f"event: {event_type}\ndata: {data}\n\n"
    finally:
        event_hub.unsubscribe(queue)


@router.get("")
async def events_stream(
    request: Request,
    _: Usuario = Depends(get_current_user),
) -> StreamingResponse:
    return StreamingResponse(
        _sse_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

import logging
import time
import uuid
from collections import defaultdict, deque
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from services.auth import ACCESS_TOKEN_COOKIE, decode_access_token

logger = logging.getLogger("escribania.access")

MAX_BODY_BYTES = 1_048_576
RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_MAX_REQUESTS = 120
AUTH_RATE_LIMIT_MAX_REQUESTS = 20


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        started = time.perf_counter()

        response = await call_next(request)
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        user_id = getattr(request.state, "user_id", None)

        logger.info(
            "request completed",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "action": f"{request.method} {request.url.path}",
                "result": "success" if response.status_code < 400 else "error",
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        response.headers["X-Request-ID"] = request_id
        return response


class MaxBodySizeMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, max_body_bytes: int = MAX_BODY_BYTES) -> None:
        super().__init__(app)
        self.max_body_bytes = max_body_bytes

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_body_bytes:
            return JSONResponse(
                status_code=413,
                content={"detail": "Request body too large"},
            )
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        *,
        window_seconds: int = RATE_LIMIT_WINDOW_SECONDS,
        max_requests: int = RATE_LIMIT_MAX_REQUESTS,
        auth_max_requests: int = AUTH_RATE_LIMIT_MAX_REQUESTS,
    ) -> None:
        super().__init__(app)
        self.window_seconds = window_seconds
        self.max_requests = max_requests
        self.auth_max_requests = auth_max_requests
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def _client_key(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"

    def _is_limited(self, key: str, limit: int) -> bool:
        now = time.time()
        bucket = self._hits[key]
        while bucket and now - bucket[0] > self.window_seconds:
            bucket.popleft()
        if len(bucket) >= limit:
            return True
        bucket.append(now)
        return False

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        limit = (
            self.auth_max_requests
            if request.url.path.startswith("/api/v1/auth/")
            else self.max_requests
        )
        bucket_key = f"{self._client_key(request)}:{request.url.path}"
        if self._is_limited(bucket_key, limit):
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests"},
            )
        return await call_next(request)


def attach_user_id_from_cookie(request: Request) -> None:
    settings = request.app.state.settings
    token = request.cookies.get(ACCESS_TOKEN_COOKIE)
    if not token:
        return
    try:
        user_id = decode_access_token(token, settings)
        request.state.user_id = str(user_id)
    except Exception:
        return


class UserContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        attach_user_id_from_cookie(request)
        return await call_next(request)

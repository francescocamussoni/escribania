from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.router import api_router
from config import get_settings
from events.publisher import event_hub
from middleware.logging_config import configure_logging
from middleware.security import (
    MaxBodySizeMiddleware,
    RateLimitMiddleware,
    RequestContextMiddleware,
    UserContextMiddleware,
)

configure_logging()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await event_hub.start()
    yield
    await event_hub.stop()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Contaduría Escribanía API", version="1.0.0", lifespan=lifespan)
    app.state.settings = settings

    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(MaxBodySizeMiddleware)
    app.add_middleware(UserContextMiddleware)
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/v1/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()

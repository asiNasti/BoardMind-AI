from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from backend.app.api.routers.chat import router as chat_router
from backend.app.api.routers.documents import router as documents_router
from backend.app.api.routers.games import router as games_router
from backend.app.api.routers.health import router as health_router
from backend.app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.http_client = httpx.AsyncClient(
        base_url=settings.gemini_api_base_url,
        timeout=settings.http_timeout,
    )
    yield
    await app.state.http_client.aclose()


app = FastAPI(title="BoardMind AI", version="1.0.0", lifespan=lifespan)

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(games_router)
app.include_router(documents_router)

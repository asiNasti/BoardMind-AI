import httpx
from fastapi import FastAPI
from collections.abc import AsyncGenerator

from backend.app.config import settings
from backend.app.api.routers.chat import router as chat_router
from backend.app.api.routers.health import router as health_router


async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    app.state.http_client = httpx.AsyncClient(
        base_url=settings.gemini_api_base_url,
        timeout=settings.http_timeout,
    )
    yield
    await app.state.http_client.aclose()

app = FastAPI(
    title='BoardMind AI',
    version='1.0.0',
    lifespan=lifespan
)

app.include_router(health_router)
app.include_router(chat_router)


import httpx
from fastapi import FastAPI
from collections.abc import AsyncGenerator

from app.config import settings


async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    app.state.http_client = httpx.AsyncClient(
        base_url=settings.api_base_url,
        timeout=settings.http_timeout,
    )
    yield
    await app.state.http_client.aclose()

app = FastAPI(
    title='BoardMind AI',
    version='1.0.0',
    lifespan=lifespan
)


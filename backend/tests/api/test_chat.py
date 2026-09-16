from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import FastAPI

from backend.app.api.routers.chat import get_rag_service, router as chat_router
from backend.app.services.gemini_client import GeminiClientError
from backend.app.services.rag_service import RAGService


@pytest.mark.asyncio
async def test_chat_maps_missing_session_to_404() -> None:
    app = FastAPI()
    app.include_router(chat_router)
    service = AsyncMock(spec=RAGService)
    service.query.side_effect = ValueError("Chat session was not found")
    app.dependency_overrides[get_rag_service] = lambda: service

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/chat/sessions/3/messages", json={"content": "How do turns work?"}
        )

    assert response.status_code == 404
    assert response.json() == {"detail": "Chat session was not found"}


@pytest.mark.asyncio
async def test_chat_maps_gemini_error_to_503() -> None:
    app = FastAPI()
    app.include_router(chat_router)
    service = AsyncMock(spec=RAGService)
    service.query.side_effect = GeminiClientError("internal provider details")
    app.dependency_overrides[get_rag_service] = lambda: service

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/chat/sessions/3/messages", json={"content": "How do turns work?"}
        )

    assert response.status_code == 503
    assert response.json() == {"detail": "AI service unavailable"}
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import FastAPI

from backend.app.api.routers.chat import (
    get_chat_service,
    get_rag_service,
    router as chat_router,
)
from backend.app.services.chat_service import ChatService
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


@pytest.mark.asyncio
async def test_create_chat_session() -> None:
    app = FastAPI()
    app.include_router(chat_router)
    service = AsyncMock(spec=ChatService)
    service.create_session.return_value = SimpleNamespace(
        id=3,
        game_id=7,
        created_at=datetime.now(timezone.utc),
    )
    app.dependency_overrides[get_chat_service] = lambda: service

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/chat/sessions/", json={"game_id": 7})

    assert response.status_code == 201
    assert response.json()["id"] == 3
    service.create_session.assert_awaited_once_with(7)


@pytest.mark.asyncio
async def test_list_chat_messages() -> None:
    app = FastAPI()
    app.include_router(chat_router)
    service = AsyncMock(spec=ChatService)
    service.list_messages.return_value = [
        SimpleNamespace(
            id=4,
            session_id=3,
            role="user",
            content="How do turns work?",
            created_at=datetime.now(timezone.utc),
        )
    ]
    app.dependency_overrides[get_chat_service] = lambda: service

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/chat/sessions/3/messages/")

    assert response.status_code == 200
    assert response.json()[0]["content"] == "How do turns work?"
    service.list_messages.assert_awaited_once_with(3)
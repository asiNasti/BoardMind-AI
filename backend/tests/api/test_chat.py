from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.routers.chat import (
    get_chat_service,
    get_rag_service,
)
from backend.app.api.routers.chat import (
    router as chat_router,
)
from backend.app.db.base import Base
from backend.app.db.database import async_session_factory, engine, get_db_session
from backend.app.db.models import ChatMessage, ChatSession, Game
from backend.app.services.chat_service import ChatService
from backend.app.services.gemini_client import GeminiClientError
from backend.app.services.rag_service import RAGService


@pytest_asyncio.fixture
async def chat_db_session() -> AsyncGenerator[AsyncSession, None]:
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
            await connection.run_sync(Base.metadata.create_all)
    except (SQLAlchemyError, OSError) as exc:
        pytest.skip(f"PostgreSQL is not available: {exc}")

    try:
        async with async_session_factory() as session:
            yield session
    finally:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
        await engine.dispose()


@pytest_asyncio.fixture
async def chat_client(
    chat_db_session: AsyncSession,
) -> AsyncGenerator[httpx.AsyncClient, None]:
    app = FastAPI()
    app.include_router(chat_router)

    async def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        yield chat_db_session

    app.dependency_overrides[get_db_session] = override_get_db_session

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


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


@pytest.mark.asyncio
async def test_create_chat_session_links_session_to_existing_game(
    chat_client: httpx.AsyncClient,
    chat_db_session: AsyncSession,
) -> None:
    game = Game(title="Root")
    chat_db_session.add(game)
    await chat_db_session.commit()
    await chat_db_session.refresh(game)

    response = await chat_client.post("/api/chat/sessions/", json={"game_id": game.id})

    assert response.status_code == 201
    assert response.json()["game_id"] == game.id
    stored_session = await chat_db_session.get(ChatSession, response.json()["id"])
    assert stored_session is not None
    assert stored_session.game_id == game.id


@pytest.mark.asyncio
async def test_list_chat_messages_returns_ascending_history(
    chat_client: httpx.AsyncClient,
    chat_db_session: AsyncSession,
) -> None:
    game = Game(title="Root")
    session = ChatSession(game=game)
    session.messages.extend(
        [
            ChatMessage(role="assistant", content="First answer"),
            ChatMessage(role="user", content="Second question"),
        ]
    )
    chat_db_session.add(session)
    await chat_db_session.commit()
    await chat_db_session.refresh(session)

    response = await chat_client.get(f"/api/chat/sessions/{session.id}/messages/")

    assert response.status_code == 200
    assert [message["content"] for message in response.json()] == [
        "First answer",
        "Second question",
    ]

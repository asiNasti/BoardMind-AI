from collections.abc import AsyncGenerator

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.routers.games import router as games_router
from backend.app.db.base import Base
from backend.app.db.database import async_session_factory, engine, get_db_session
from backend.app.db.models import Document, Game


@pytest_asyncio.fixture
async def test_db_session() -> AsyncGenerator[AsyncSession, None]:
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
async def client(
    test_db_session: AsyncSession,
) -> AsyncGenerator[httpx.AsyncClient, None]:
    test_app = FastAPI()
    test_app.include_router(games_router)

    async def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        yield test_db_session

    test_app.dependency_overrides[get_db_session] = override_get_db_session

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=test_app), base_url="http://test"
    ) as async_client:
        yield async_client


@pytest.mark.asyncio
async def test_create_and_list_games(client: httpx.AsyncClient) -> None:
    create_response = await client.post(
        "/api/games/",
        json={"title": "Root", "description": "A forest strategy game"},
    )

    assert create_response.status_code == 201
    created_game = create_response.json()
    assert created_game["title"] == "Root"
    assert created_game["description"] == "A forest strategy game"
    assert created_game["id"] > 0

    list_response = await client.get("/api/games/")

    assert list_response.status_code == 200
    assert list_response.json() == [created_game]


@pytest.mark.asyncio
async def test_list_documents_for_game(
    client: httpx.AsyncClient, test_db_session: AsyncSession
) -> None:
    game = Game(title="Root")
    game.documents.append(Document(filename="root-rules.pdf"))
    test_db_session.add(game)
    await test_db_session.commit()
    await test_db_session.refresh(game)

    response = await client.get(f"/api/games/{game.id}/documents/")

    assert response.status_code == 200
    assert response.json()[0]["game_id"] == game.id
    assert response.json()[0]["filename"] == "root-rules.pdf"


@pytest.mark.asyncio
async def test_list_documents_returns_404_for_unknown_game(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get("/api/games/999999/documents/")

    assert response.status_code == 404
    assert response.json() == {"detail": "Game 999999 not found"}

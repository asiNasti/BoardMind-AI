from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.app.services.chat_service import ChatService


@pytest.mark.asyncio
async def test_create_session_persists_session_for_existing_game() -> None:
    db = MagicMock()
    db.get = AsyncMock(return_value=SimpleNamespace(id=7))
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    service = ChatService(db)

    result = await service.create_session(7)

    assert result.game_id == 7
    db.add.assert_called_once_with(result)
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(result)


@pytest.mark.asyncio
async def test_create_session_rejects_unknown_game() -> None:
    db = MagicMock()
    db.get = AsyncMock(return_value=None)
    service = ChatService(db)

    with pytest.raises(ValueError, match="Game 7 not found"):
        await service.create_session(7)

    db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_list_messages_returns_messages_in_query_order() -> None:
    db = MagicMock()
    messages = [SimpleNamespace(id=1), SimpleNamespace(id=2)]
    result = MagicMock()
    result.scalars.return_value.all.return_value = messages
    db.get = AsyncMock(return_value=SimpleNamespace(id=3))
    db.execute = AsyncMock(return_value=result)
    service = ChatService(db)

    assert await service.list_messages(3) == messages
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_messages_rejects_unknown_session() -> None:
    db = MagicMock()
    db.get = AsyncMock(return_value=None)
    service = ChatService(db)

    with pytest.raises(ValueError, match="Chat session 3 not found"):
        await service.list_messages(3)

    db.execute.assert_not_called()

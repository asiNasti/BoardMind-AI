from collections import namedtuple
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.app.services.gemini_client import GeminiClientError
from backend.app.services.rag_service import OFF_TOPIC_MESSAGE, RAGService


@pytest.mark.asyncio
async def test_query_returns_exact_off_topic_message_without_llm_call() -> None:
    db = MagicMock()
    db.get = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.get.return_value = SimpleNamespace(game_id=7)
    result = MagicMock()
    retrieved_row = namedtuple("RetrievedRow", ["chunk", "distance"])
    result.all.return_value = [
        retrieved_row(SimpleNamespace(content="Turn order"), 0.9),
    ]
    db.execute.return_value = result
    client = AsyncMock()
    client.generate_embeddings.return_value = [0.1, 0.2]

    service = RAGService(db, client, similarity_threshold=0.35)

    result = await service.query(3, "What is the price of a spaceship?")

    assert result == OFF_TOPIC_MESSAGE
    client.generate_response.assert_not_awaited()
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_query_propagates_gemini_client_error() -> None:
    db = MagicMock()
    db.get = AsyncMock(return_value=SimpleNamespace(game_id=7))
    db.commit = AsyncMock()
    client = AsyncMock()
    client.generate_embeddings.side_effect = GeminiClientError(
        "Gemini API request failed"
    )

    service = RAGService(db, client)

    with pytest.raises(GeminiClientError, match="request failed"):
        await service.query(3, "How do turns work?")

    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_query_rejects_missing_chat_session() -> None:
    db = MagicMock()
    db.get = AsyncMock(return_value=None)
    client = AsyncMock()

    service = RAGService(db, client)

    with pytest.raises(ValueError, match="Chat session was not found"):
        await service.query(3, "How do turns work?")

    client.generate_embeddings.assert_not_awaited()


def test_build_prompt_contains_context_history_and_guardrail() -> None:
    history = [SimpleNamespace(role="user", content="How do turns work?")]

    prompt = RAGService.build_prompt(
        "Can I pass?", ["A player may pass once."], history
    )

    assert "A player may pass once." in prompt
    assert "user: How do turns work?" in prompt
    assert "The rules do not mention this" in prompt


@pytest.mark.asyncio
async def test_query_logs_off_topic_event(caplog) -> None:
    db = MagicMock()
    db.get = AsyncMock(return_value=SimpleNamespace(game_id=7))
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    result = MagicMock()
    retrieved_row = namedtuple("RetrievedRow", ["chunk", "distance"])
    result.all.return_value = [
        retrieved_row(SimpleNamespace(content="Turn order"), 0.9)
    ]
    db.execute.return_value = result
    client = AsyncMock()
    client.generate_embeddings.return_value = [0.1, 0.2]

    service = RAGService(db, client, similarity_threshold=0.35)

    with caplog.at_level("INFO"):
        await service.query(3, "What is the price of a spaceship?")

    assert "off_topic_query" in caplog.text
    assert '"session_id": 3' in caplog.text

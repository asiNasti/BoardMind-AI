from collections import namedtuple
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

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


def test_build_prompt_contains_context_history_and_guardrail() -> None:
    history = [SimpleNamespace(role="user", content="How do turns work?")]

    prompt = RAGService.build_prompt("Can I pass?", ["A player may pass once."], history)

    assert "A player may pass once." in prompt
    assert "user: How do turns work?" in prompt
    assert "The rules do not mention this" in prompt
import httpx
import pytest
import respx
from sqlalchemy import select

from backend.app.db.models import Document, DocumentChunk, Game
from backend.app.services.gemini_client import GeminiClient
from backend.app.services.ingestion_service import IngestionService
from backend.app.services.pdf_parser import chunk_text

BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
API_KEY = "test-api-key"


def test_chunk_text_splits_on_size_with_overlap() -> None:
    text = "word " * 500

    chunks = chunk_text(text, chunk_size=700, overlap=100)

    assert len(chunks) >= 2
    assert all(0 < len(chunk) <= 700 for chunk in chunks)
    assert len(chunks[0]) <= 700
    assert len(chunks[1]) <= 700
    assert chunks[0].startswith("word")
    assert chunks[1].startswith("word")
    assert chunks[0][:100] == chunks[1][:100] or chunks[0][-100:] == chunks[1][:100]


@pytest.mark.asyncio
async def test_ingest_document_generates_embeddings_and_persists_chunks(
    test_db_session,
    monkeypatch,
) -> None:
    game = Game(title="Root")
    test_db_session.add(game)
    await test_db_session.commit()
    await test_db_session.refresh(game)

    large_text = "A player may move one unit per turn. " * 50
    monkeypatch.setattr(
        "backend.app.services.ingestion_service.extract_text_from_pdf",
        lambda _pdf_bytes: large_text,
    )

    with respx.mock(base_url=BASE_URL, assert_all_mocked=True) as router:
        route = router.post("/models/text-embedding-004:embedContent").mock(
            side_effect=[
                httpx.Response(200, json={"embedding": {"values": [0.1] * 768}}),
                httpx.Response(200, json={"embedding": {"values": [0.2] * 768}}),
                httpx.Response(200, json={"embedding": {"values": [0.3] * 768}}),
            ]
        )

        service = IngestionService(
            test_db_session,
            GeminiClient(api_key=API_KEY, base_url=BASE_URL),
        )

        document = await service.ingest_document(game.id, "rules.pdf", b"%PDF-1.4")

    assert document.filename == "rules.pdf"
    assert document.game_id == game.id
    assert route.called

    stored = await test_db_session.execute(
        select(DocumentChunk)
        .where(DocumentChunk.document_id == document.id)
        .order_by(DocumentChunk.chunk_index)
    )
    chunks = stored.scalars().all()
    assert len(chunks) == 3
    assert all(len(chunk.embedding) == 768 for chunk in chunks)
    assert all(chunk.content for chunk in chunks)

    count = await test_db_session.scalar(
        select(Document.id).where(Document.id == document.id)
    )
    assert count == document.id

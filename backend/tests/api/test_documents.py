from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import FastAPI, Request

from backend.app.api.routers.documents import (
    get_ingestion_service,
)
from backend.app.api.routers.documents import (
    router as documents_router,
)
from backend.app.services.gemini_client import GeminiClientError
from backend.app.services.ingestion_service import IngestionService


def create_app(service: IngestionService) -> FastAPI:
    app = FastAPI()
    app.include_router(documents_router)
    app.dependency_overrides[get_ingestion_service] = lambda: service
    return app


@pytest.mark.asyncio
async def test_upload_document_rejects_non_pdf() -> None:
    service = AsyncMock(spec=IngestionService)
    app = create_app(service)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/games/7/documents/",
            files={"file": ("rules.txt", b"not a PDF", "text/plain")},
        )

    assert response.status_code == 400
    assert response.json() == {"detail": "Only PDF files are supported"}
    service.ingest_document.assert_not_awaited()


@pytest.mark.asyncio
async def test_upload_document_returns_created_document() -> None:
    service = AsyncMock(spec=IngestionService)
    service.ingest_document.return_value = SimpleNamespace(
        id=4,
        game_id=7,
        filename="rules.pdf",
        uploaded_at=datetime.now(timezone.utc),
    )
    app = create_app(service)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/games/7/documents/",
            files={"file": ("rules.pdf", b"%PDF-1.4", "application/pdf")},
        )

    assert response.status_code == 201
    assert response.json()["filename"] == "rules.pdf"
    service.ingest_document.assert_awaited_once_with(7, "rules.pdf", b"%PDF-1.4")


@pytest.mark.asyncio
async def test_upload_document_maps_ingestion_error_to_400() -> None:
    service = AsyncMock(spec=IngestionService)
    service.ingest_document.side_effect = ValueError("No text could be extracted")
    app = create_app(service)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/games/7/documents/",
            files={"file": ("rules.pdf", b"%PDF-1.4", "application/pdf")},
        )

    assert response.status_code == 400
    assert response.json() == {"detail": "No text could be extracted"}


@pytest.mark.asyncio
async def test_upload_document_maps_gemini_error_to_503() -> None:
    service = AsyncMock(spec=IngestionService)
    service.ingest_document.side_effect = GeminiClientError("provider unavailable")
    app = create_app(service)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/games/7/documents/",
            files={"file": ("rules.pdf", b"%PDF-1.4", "application/pdf")},
        )

    assert response.status_code == 503
    assert response.json() == {"detail": "AI service unavailable"}


@pytest.mark.asyncio
@pytest.mark.parametrize("http_client", [None, object()])
async def test_get_ingestion_service_builds_service(http_client) -> None:
    app = FastAPI()
    app.state.http_client = http_client
    request = Request({"type": "http", "app": app})

    service = await get_ingestion_service(request, MagicSession())

    assert isinstance(service, IngestionService)
    assert service.session.__class__ is MagicSession


class MagicSession:
    pass

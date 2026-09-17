from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.schemas import DocumentResponse
from backend.app.db.database import get_db_session
from backend.app.services.gemini_client import GeminiClient, GeminiClientError
from backend.app.services.ingestion_service import IngestionService

router = APIRouter(prefix="/api/games", tags=["documents"])


async def get_ingestion_service(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> IngestionService:
    http_client = getattr(request.app.state, "http_client", None)
    client = GeminiClient(http_client=http_client) if http_client is not None else GeminiClient()
    return IngestionService(session, client)


@router.post("/{game_id}/documents/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    game_id: int,
    file: UploadFile = File(...),
    service: IngestionService = Depends(get_ingestion_service),
) -> DocumentResponse:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are supported")

    pdf_bytes = await file.read()
    try:
        document = await service.ingest_document(game_id, file.filename, pdf_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except GeminiClientError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI service unavailable") from exc

    return DocumentResponse.model_validate(document)

from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.database import get_db_session
from backend.app.services.gemini_client import GeminiClient, GeminiClientError
from backend.app.services.rag_service import RAGService

router = APIRouter(prefix="/api/chat", tags=["chat"])


class MessageRequest(BaseModel):
    content: str = Field(min_length=1)


class MessageResponse(BaseModel):
    content: str


async def get_rag_service(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> AsyncGenerator[RAGService, None]:
    client = GeminiClient(http_client=request.app.state.http_client)
    yield RAGService(session, client)


@router.post("/sessions/{session_id}/messages", response_model=MessageResponse)
async def send_message(
    session_id: int,
    message: MessageRequest,
    service: RAGService = Depends(get_rag_service),
) -> MessageResponse:
    try:
        answer = await service.query(session_id, message.content)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except GeminiClientError as exc:
        raise HTTPException(status_code=503, detail="AI service unavailable") from exc
    return MessageResponse(content=answer)
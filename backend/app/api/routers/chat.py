from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.database import get_db_session
from backend.app.services.gemini_client import GeminiClient
from backend.app.services.rag_service import RAGService

router = APIRouter(prefix="/api/chat", tags=["chat"])


class MessageRequest(BaseModel):
    content: str = Field(min_length=1)


class MessageResponse(BaseModel):
    content: str


async def get_rag_service(
    session: AsyncSession = Depends(get_db_session),
) -> AsyncGenerator[RAGService, None]:
    client = GeminiClient()
    try:
        yield RAGService(session, client)
    finally:
        await client.aclose()


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
    return MessageResponse(content=answer)
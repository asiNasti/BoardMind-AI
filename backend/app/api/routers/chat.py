from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.schemas import (
    ChatMessageResponse,
    ChatSessionCreate,
    ChatSessionResponse,
)
from backend.app.db.database import get_db_session
from backend.app.services.chat_service import ChatService
from backend.app.services.gemini_client import GeminiClient, GeminiClientError
from backend.app.services.rag_service import RAGService

router = APIRouter(prefix="/api/chat", tags=["chat"])


class MessageRequest(BaseModel):
    content: str = Field(min_length=1)


class MessageResponse(BaseModel):
    content: str


def get_chat_service(session: AsyncSession = Depends(get_db_session)) -> ChatService:
    return ChatService(session)


async def get_rag_service(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> AsyncGenerator[RAGService, None]:
    client = GeminiClient(http_client=request.app.state.http_client)
    yield RAGService(session, client)


@router.post("/sessions/", response_model=ChatSessionResponse, status_code=201)
async def create_chat_session(
    session_data: ChatSessionCreate,
    service: ChatService = Depends(get_chat_service),
) -> ChatSessionResponse:
    try:
        return await service.create_session(session_data.game_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/sessions/{session_id}/messages/", response_model=list[ChatMessageResponse])
async def list_chat_messages(
    session_id: int,
    service: ChatService = Depends(get_chat_service),
) -> list[ChatMessageResponse]:
    try:
        return await service.list_messages(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


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
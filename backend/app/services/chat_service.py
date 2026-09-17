from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models import ChatMessage, ChatSession, Game


class ChatService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_session(self, game_id: int) -> ChatSession:
        game = await self.session.get(Game, game_id)
        if game is None:
            raise ValueError(f"Game {game_id} not found")

        chat_session = ChatSession(game_id=game_id)
        self.session.add(chat_session)
        await self.session.commit()
        await self.session.refresh(chat_session)
        return chat_session

    async def list_messages(self, session_id: int) -> list[ChatMessage]:
        chat_session = await self.session.get(ChatSession, session_id)
        if chat_session is None:
            raise ValueError(f"Chat session {session_id} not found")

        result = await self.session.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at, ChatMessage.id)
        )
        return list(result.scalars().all())

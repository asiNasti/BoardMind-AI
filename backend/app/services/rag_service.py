from collections.abc import Sequence

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models import ChatMessage, ChatSession, Document, DocumentChunk
from backend.app.services.gemini_client import GeminiClient

OFF_TOPIC_MESSAGE = "This question is unrelated to the game rules."
UNKNOWN_RULE_MESSAGE = "The rules do not mention this"


class RAGService:
    """Coordinates retrieval, guardrails, prompt construction, and chat persistence."""

    def __init__(
        self,
        session: AsyncSession,
        gemini_client: GeminiClient,
        similarity_threshold: float = 0.35,
        top_k: int = 5,
        history_limit: int = 5,
    ) -> None:
        self.session = session
        self.gemini_client = gemini_client
        self.similarity_threshold = similarity_threshold
        self.top_k = top_k
        self.history_limit = history_limit

    async def query(self, session_id: int, content: str) -> str:
        chat_session = await self.session.get(ChatSession, session_id)
        if chat_session is None:
            raise ValueError("Chat session was not found")

        query_embedding = await self.gemini_client.generate_embeddings(content)
        distance = DocumentChunk.embedding.cosine_distance(query_embedding).label("distance")
        statement = (
            select(DocumentChunk, distance)
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(Document.game_id == chat_session.game_id)
            .order_by(distance)
            .limit(self.top_k)
        )
        retrieved = (await self.session.execute(statement)).all()

        if not retrieved or float(retrieved[0].distance) > self.similarity_threshold:
            answer = OFF_TOPIC_MESSAGE
        else:
            history = await self._recent_messages(session_id)
            prompt = self.build_prompt(content, [chunk.content for chunk, _ in retrieved], history)
            answer = await self.gemini_client.generate_response(prompt)

        await self._save_messages(session_id, content, answer)
        return answer

    async def _save_messages(self, session_id: int, content: str, answer: str) -> None:
        self.session.add(ChatMessage(session_id=session_id, role="user", content=content))
        self.session.add(ChatMessage(session_id=session_id, role="assistant", content=answer))
        await self.session.commit()

    async def _recent_messages(self, session_id: int) -> list[ChatMessage]:
        statement = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(desc(ChatMessage.created_at), desc(ChatMessage.id))
            .limit(self.history_limit)
        )
        messages = list((await self.session.scalars(statement)).all())
        messages.reverse()
        return messages

    @staticmethod
    def build_prompt(
        question: str,
        chunks: Sequence[str],
        history: Sequence[ChatMessage],
    ) -> str:
        context = "\n\n".join(f"[Rule {index}] {chunk}" for index, chunk in enumerate(chunks, 1))
        history_text = "\n".join(f"{message.role}: {message.content}" for message in history)
        return (
            "You are a board game referee. Answer only from the provided context. "
            f"If the answer is not in the context, say: {UNKNOWN_RULE_MESSAGE}.\n\n"
            f"CONTEXT:\n{context}\n\n"
            f"CHAT HISTORY:\n{history_text or '(empty)'}\n\n"
            f"QUESTION:\n{question}"
        )
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models import Document, DocumentChunk, Game
from backend.app.services.gemini_client import GeminiClient
from backend.app.services.pdf_parser import chunk_text, extract_text_from_pdf


class IngestionService:
    def __init__(self, session: AsyncSession, gemini_client: GeminiClient) -> None:
        self.session = session
        self.gemini_client = gemini_client

    async def ingest_document(
        self, game_id: int, filename: str, file_bytes: bytes
    ) -> Document:
        game = await self.session.get(Game, game_id)
        if game is None:
            raise ValueError(f"Game {game_id} not found")

        if not filename.lower().endswith(".pdf"):
            raise ValueError("Only PDF files are supported")

        text = extract_text_from_pdf(file_bytes)
        chunks = chunk_text(text)
        if not chunks:
            raise ValueError("No text could be extracted from the PDF")

        document = Document(game_id=game_id, filename=filename)
        self.session.add(document)
        await self.session.flush()

        for index, chunk in enumerate(chunks):
            embedding = await self.gemini_client.generate_embeddings(chunk)
            self.session.add(
                DocumentChunk(
                    document_id=document.id,
                    content=chunk,
                    embedding=embedding,
                    chunk_index=index,
                )
            )

        await self.session.commit()
        await self.session.refresh(document)
        return document

    async def list_chunks_for_document(self, document_id: int) -> list[DocumentChunk]:
        result = await self.session.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
        )
        return list(result.scalars().all())

    async def ingest_document_from_bytes(
        self, game_id: int, filename: str, file_bytes: bytes
    ) -> Document:
        return await self.ingest_document(game_id, filename, file_bytes)

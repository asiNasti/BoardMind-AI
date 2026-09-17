from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logger import get_logger
from backend.app.db.models import Document, DocumentChunk, Game
from backend.app.services.gemini_client import GeminiClient
from backend.app.services.pdf_parser import chunk_text, extract_text_from_pdf

logger = get_logger(__name__)


class IngestionService:
    def __init__(self, session: AsyncSession, gemini_client: GeminiClient) -> None:
        self.session = session
        self.gemini_client = gemini_client

    async def ingest_document(
        self, game_id: int, filename: str, file_bytes: bytes
    ) -> Document:
        logger.info(
            "ingestion_started",
            game_id=game_id,
            filename=filename,
            file_size_bytes=len(file_bytes),
        )
        game = await self.session.get(Game, game_id)
        if game is None:
            logger.warning("game_not_found_for_ingestion", game_id=game_id)
            raise ValueError(f"Game {game_id} not found")

        if not filename.lower().endswith(".pdf"):
            logger.warning("invalid_document_type", game_id=game_id, filename=filename)
            raise ValueError("Only PDF files are supported")

        text = extract_text_from_pdf(file_bytes)
        chunks = chunk_text(text)
        if not chunks:
            logger.warning("pdf_extraction_produced_no_text", game_id=game_id)
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
        logger.info(
            "ingestion_completed",
            game_id=game_id,
            document_id=document.id,
            chunk_count=len(chunks),
        )
        return document

    async def list_chunks_for_document(self, document_id: int) -> list[DocumentChunk]:
        result = await self.session.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
        )
        chunks = list(result.scalars().all())
        logger.info(
            "document_chunks_loaded",
            document_id=document_id,
            chunk_count=len(chunks),
        )
        return chunks

    async def ingest_document_from_bytes(
        self, game_id: int, filename: str, file_bytes: bytes
    ) -> Document:
        return await self.ingest_document(game_id, filename, file_bytes)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.schemas import GameCreate
from backend.app.db.models import Document, Game


class GameService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_games(self) -> list[Game]:
        result = await self.session.execute(select(Game).order_by(Game.id))
        return list(result.scalars().all())

    async def create_game(self, game_data: GameCreate) -> Game:
        game = Game(title=game_data.title, description=game_data.description)
        self.session.add(game)
        await self.session.commit()
        await self.session.refresh(game)
        return game

    async def list_documents(self, game_id: int) -> list[Document]:
        game = await self.session.get(Game, game_id)
        if game is None:
            raise ValueError(f"Game {game_id} not found")

        result = await self.session.execute(
            select(Document).where(Document.game_id == game_id).order_by(Document.id)
        )
        return list(result.scalars().all())
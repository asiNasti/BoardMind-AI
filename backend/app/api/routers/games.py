from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.schemas import DocumentResponse, GameCreate, GameResponse
from backend.app.db.database import get_db_session
from backend.app.services.game_service import GameService

router = APIRouter(prefix="/api/games", tags=["games"])


def get_game_service(session: AsyncSession = Depends(get_db_session)) -> GameService:
    return GameService(session)


@router.get("/", response_model=list[GameResponse])
async def list_games(service: GameService = Depends(get_game_service)) -> list[GameResponse]:
    return await service.list_games()


@router.post("/", response_model=GameResponse, status_code=status.HTTP_201_CREATED)
async def create_game(
    game_data: GameCreate,
    service: GameService = Depends(get_game_service),
) -> GameResponse:
    return await service.create_game(game_data)


@router.get("/{game_id}/documents/", response_model=list[DocumentResponse])
async def list_documents(
    game_id: int,
    service: GameService = Depends(get_game_service),
) -> list[DocumentResponse]:
    try:
        return await service.list_documents(game_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
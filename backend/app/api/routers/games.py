from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.schemas import DocumentResponse, GameCreate, GameResponse
from backend.app.db.database import get_db_session
from backend.app.services.game_service import GameService

router = APIRouter(prefix="/api/games", tags=["games"])


def get_game_service(
    session: AsyncSession = Depends(get_db_session),  # noqa: B008
) -> GameService:
    return GameService(session)


@router.get("/", response_model=list[GameResponse])
async def list_games(
    service: GameService = Depends(get_game_service),  # noqa: B008
) -> list[GameResponse]:
    games = await service.list_games()
    return [GameResponse.model_validate(game) for game in games]


@router.post("/", response_model=GameResponse, status_code=status.HTTP_201_CREATED)
async def create_game(
    game_data: GameCreate,
    service: GameService = Depends(get_game_service),  # noqa: B008
) -> GameResponse:
    game = await service.create_game(game_data)
    return GameResponse.model_validate(game)


@router.get("/{game_id}/documents/", response_model=list[DocumentResponse])
async def list_documents(
    game_id: int,
    service: GameService = Depends(get_game_service),  # noqa: B008
) -> list[DocumentResponse]:
    try:
        documents = await service.list_documents(game_id)
        return [DocumentResponse.model_validate(document) for document in documents]
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc

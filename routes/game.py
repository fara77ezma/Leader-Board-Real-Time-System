from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from config.db import get_db
from controllers import game, auth
from models.request import CreateGameRequest

security = HTTPBearer()

router = APIRouter(
    prefix="/game",
    tags=["Game"],
)


@router.post("/")
async def create_game(
    request: CreateGameRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    await auth.require_admin(credentials, db)
    return game.create_new_game(request=request, db=db)


@router.get("/")
async def get_all_games(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    await auth.require_admin(credentials, db)
    return game.get_games(db=db)


@router.get("/list")
async def get_active_games(
    db: Session = Depends(get_db),
):
    return game.get_games(db=db, is_active=True)


@router.patch("/deactivate/{game_name}")
async def deactivate_game(
    game_name: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    await auth.require_admin(credentials, db)
    return game.deactivate_game(game_name=game_name, db=db)


@router.patch("/activate/{game_name}")
async def activate_game(
    game_name: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    await auth.require_admin(credentials, db)
    return game.activate_game(game_name=game_name, db=db)


@router.delete("/{game_name}")
async def delete_game(
    game_name: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    await auth.require_admin(credentials, db)
    return game.delete_game(game_name=game_name, db=db)

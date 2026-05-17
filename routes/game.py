from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from config.db import get_db
from controllers import users, game
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
    current_user = await users.get_current_user(credentials=credentials, db=db)
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required.",
        )
    return game.create_new_game(request=request, db=db)

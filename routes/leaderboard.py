from fastapi import APIRouter, Depends, Request
from config.db import get_db
from sqlalchemy.orm import Session
from models.request import SubmitScoreRequest
from controllers import users
from controllers.leaderboard import fetch_leaderboard, fetch_user_rank, submit_score

router = APIRouter(
    prefix="/leaderboard",
)


@router.post("/api/submit-score")
async def submit_new_score(
    request: SubmitScoreRequest,
    db: Session = Depends(get_db),
):
    current_user = await users.get_current_user(request=request, db=db)
    return submit_score(request=request, current_user=current_user, db=db)


@router.get("/api/get-leaderboard/{game_id}")
def get_leaderboard(game_id: str, db: Session = Depends(get_db), limit: int = 10):
    return fetch_leaderboard(game_id=game_id, limit=limit, db=db)


@router.get("/api/get-leaderboard/{game_id}/user-rank")
async def get_user_rank(
    game_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    current_user = await users.get_current_user(request=request, db=db)
    return fetch_user_rank(game_id=game_id, current_user=current_user)

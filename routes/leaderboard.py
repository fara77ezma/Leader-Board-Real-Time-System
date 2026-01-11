from fastapi import APIRouter, Depends
from db.db import get_db
from sqlalchemy.orm import Session
from models.request import SubmitScoreRequest
from controllers.users import get_current_user
from controllers.leaderboard import fetch_leaderboard, fetch_user_rank, submit_score

router = APIRouter(
    prefix="/leaderboard",
)


@router.post("/api/submit-score")
def submit_new_score(
    request: SubmitScoreRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return submit_score(request=request, current_user=current_user, db=db)


@router.get("/api/get-leaderboard/{game_id}")
def get_leaderboard(game_id: str, db: Session = Depends(get_db), limit: int = 10):
    return fetch_leaderboard(game_id=game_id, limit=limit, db=db)


@router.get("/api/get-leaderboard/{game_id}/user-rank")
def get_user_rank(
    game_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return fetch_user_rank(game_id=game_id, current_user=current_user, db=db)

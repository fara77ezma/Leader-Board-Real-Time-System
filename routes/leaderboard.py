from fastapi import APIRouter, Depends, Request
from config.db import get_db
from sqlalchemy.orm import Session
from models.request import SubmitScoreRequest
from controllers import users
from controllers import leaderboard

router = APIRouter(
    prefix="/leaderboard",
)


@router.post("/api/submit-score")
async def submit_new_score(
    request: Request,
    body: SubmitScoreRequest,
    db: Session = Depends(get_db),
):
    current_user = await users.get_current_user(request=request, db=db)
    return leaderboard.submit_score(request=body, current_user=current_user, db=db)


@router.get("/api/get-leaderboard/{game_id}")
def get_leaderboard(game_id: str, db: Session = Depends(get_db), limit: int = 10):
    return leaderboard.fetch_leaderboard(game_id=game_id, limit=limit, db=db)


@router.get("/api/get-leaderboard/{game_id}/user-rank")
async def get_user_rank(
    game_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    current_user = await users.get_current_user(request=request, db=db)
    return leaderboard.fetch_user_rank(game_id=game_id, current_user=current_user)

@router.post("/api/refresh-leaderboard/{game_id}")
def refresh_leaderboard(game_id: str, db: Session = Depends(get_db)):
    return leaderboard.refresh_redis_leaderboard(game_id=game_id, db=db)

@router.post("/api/refresh-all-leaderboards")
def refresh_all_leaderboards(db: Session = Depends(get_db)):
    return leaderboard.refresh_all_leaderboards(db=db)

@router.post("/api/refresh-user-scores/{user_id}")
def refresh_user_scores(user_id: int, db: Session = Depends(get_db)):
    return leaderboard.refresh_user_scores_in_leaderboards(user_id=user_id, db=db)
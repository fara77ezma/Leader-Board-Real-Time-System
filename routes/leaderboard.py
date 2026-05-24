from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from config.db import get_db
from sqlalchemy.orm import Session
from models.request import SubmitScoreRequest
from controllers import users, leaderboard, auth

security = HTTPBearer()

router = APIRouter(
    prefix="/leaderboard",
    tags=["Leaderboard"],
)


@router.post("/api/submit-score")
async def submit_new_score(
    request: SubmitScoreRequest,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    current_user = await users.get_current_user(credentials=credentials, db=db)
    return leaderboard.submit_score(request=request, current_user=current_user, db=db)


@router.get("/api/get-leaderboard/{game_name}")
def get_leaderboard(game_name: str, db: Session = Depends(get_db), limit: int = 10):
    return leaderboard.fetch_leaderboard(game_name=game_name, limit=limit, db=db)


@router.get("/api/get-leaderboard/{game_name}/user-rank")
async def get_user_rank(
    game_name: str,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    current_user = await users.get_current_user(credentials=credentials, db=db)
    return leaderboard.fetch_user_rank(game_name=game_name, current_user=current_user)


@router.post("/api/refresh-leaderboard/{game_name}")
async def refresh_leaderboard(
    game_name: str,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    await auth.require_admin(credentials, db)
    return leaderboard.refresh_redis_leaderboard(game_name=game_name, db=db)


@router.post("/api/refresh-all-leaderboards")
async def refresh_all_leaderboards(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    await auth.require_admin(credentials, db)

    return leaderboard.refresh_all_leaderboards(db=db)


@router.post("/api/refresh-user-scores/{user_id}")
async def refresh_user_scores(
    user_id: int,
    game_name: str | None = None,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    await auth.require_admin(credentials, db)

    return leaderboard.refresh_user_scores_in_leaderboards(
        user_id=user_id, game_name=game_name, db=db
    )

@router.get("/api/get-leaderboard/{game_name}/around-me")
async def get_around_me(
    game_name: str,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    current_user = await users.get_current_user(credentials=credentials, db=db)
    return leaderboard.fetch_around_me(game_name=game_name, current_user=current_user, db=db)
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from config.db import get_db
from sqlalchemy.orm import Session
from models.request import SubmitScoreRequest
from controllers import users, leaderboard

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


@router.get("/api/get-leaderboard/{game_id}")
def get_leaderboard(game_id: str, db: Session = Depends(get_db), limit: int = 10):
    return leaderboard.fetch_leaderboard(game_id=game_id, limit=limit, db=db)


@router.get("/api/get-leaderboard/{game_id}/user-rank")
async def get_user_rank(
    game_id: str,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    current_user = await users.get_current_user(credentials=credentials, db=db)
    return leaderboard.fetch_user_rank(game_id=game_id, current_user=current_user)


@router.post("/api/refresh-leaderboard/{game_id}")
async def refresh_leaderboard(
    game_id: str,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    current_user = await users.get_current_user(credentials=credentials, db=db)
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required.",
        )
    return leaderboard.refresh_redis_leaderboard(game_id=game_id, db=db)


@router.post("/api/refresh-all-leaderboards")
async def refresh_all_leaderboards(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    current_user = await users.get_current_user(credentials=credentials, db=db)
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required.",
        )
    return leaderboard.refresh_all_leaderboards(db=db)


@router.post("/api/refresh-user-scores/{user_id}")
async def refresh_user_scores(
    user_id: int,
    game_id: int | None = None,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    current_user = await users.get_current_user(credentials=credentials, db=db)
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required.",
        )
    return leaderboard.refresh_user_scores_in_leaderboards(
        user_id=user_id, game_id=game_id, db=db
    )

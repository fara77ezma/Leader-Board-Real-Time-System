from config.cloudinary import upload_avatar
from config.db import get_db
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from models.response import DifferentUserProfileResponse, UserProfileResponse
from models.tables import User
from fastapi import UploadFile
from sqlalchemy.orm import Session
from urllib.parse import quote
from controllers.leaderboard import get_player_ranks_from_redis
from config.cloudinary import delete_avatar


security = HTTPBearer()


async def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(security)
) -> UserProfileResponse:
    from controllers.auth import verify_token

    payload = verify_token(token.credentials)
    user = db.query(User).filter(User.id == payload["user_id"]).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if "error" in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=payload["error"]
        )
    games = await get_player_ranks_from_redis(player_id=user.id)

    return UserProfileResponse(
        id=payload["user_id"],
        username=payload["username"],
        avatar_url=user.avatar_url if user.avatar_url else None,
        games=games,
        is_verified=user.is_verified,
        created_at=user.created_at,
    )


async def get_user_profile(username: str, db: Session) -> DifferentUserProfileResponse:
    user = db.query(User).filter(User.username == username).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    games = await get_player_ranks_from_redis(player_id=user.id)

    return DifferentUserProfileResponse(
        username=user.username,
        avatar_url=user.avatar_url,
        games=games,
    )


async def update_user_profile(
    db: Session,
    current_user: UserProfileResponse,
    avatar_file: UploadFile,
) -> dict:
    user = db.query(User).filter(User.id == current_user.id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    if avatar_file:
        avatar_url = await upload_avatar(avatar_file, current_user.username)
        user.avatar_url = avatar_url

    db.commit()
    db.refresh(user)
    return {"message": "avatar updated successfully."}


async def remove_user_avatar(db: Session, current_user: UserProfileResponse) -> dict:
    user = db.query(User).filter(User.id == current_user.id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    await delete_avatar(user.username)
    user.avatar_url = generate_default_avatar(username=user.username)
    db.commit()
    db.refresh(user)

    return {"message": "avatar deleted successfully."}


def generate_default_avatar(username: str) -> str:

    encoded_name = quote(username)
    return f"https://ui-avatars.com/api/?name={encoded_name}&size=200&background=random&color=fff&bold=true"

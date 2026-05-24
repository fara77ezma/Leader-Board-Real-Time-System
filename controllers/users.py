from fastapi.security import HTTPAuthorizationCredentials

from config.cloudinary import upload_avatar
from config.db import get_db
from fastapi import Depends, HTTPException, UploadFile, status
from controllers import auth
from models.response import DifferentUserProfileResponse, UserProfileResponse
from models.tables import RefreshToken, User
from sqlalchemy.orm import Session
from urllib.parse import quote
from controllers.leaderboard import get_player_ranks_from_redis
from config.cloudinary import delete_avatar
from config.redis import redis_client


async def get_current_user(
    credentials: HTTPAuthorizationCredentials, db: Session = Depends(get_db)
) -> UserProfileResponse:
    from controllers.auth import verify_token

    token = credentials.credentials
    payload = verify_token(token)
    if "error" in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=payload["error"]
        )
    user = db.query(User).filter(User.id == payload["user_id"]).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    games = await get_player_ranks_from_redis(
        db=db, player_id=user.id, player_code=user.user_code
    )

    return UserProfileResponse(
        id=payload["user_id"],
        username=payload["username"],
        avatar_url=user.avatar_url if user.avatar_url else None,
        games=games,
        is_verified=user.is_verified,
        created_at=user.created_at,
        is_admin=user.is_admin,
    )


async def get_user_profile(username: str, db: Session) -> DifferentUserProfileResponse:
    user = db.query(User).filter(User.username == username).first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    games = await get_player_ranks_from_redis(
        db=db, player_id=user.id, player_code=user.user_code
    )

    return DifferentUserProfileResponse(
        username=user.username,
        avatar_url=user.avatar_url,
        games=games,
    )


async def update_user_avatar(
    db: Session,
    current_user: UserProfileResponse,
    avatar_file: UploadFile,
) -> dict:
    user = db.query(User).filter(User.id == current_user.id).first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    if avatar_file:
        avatar_url = await upload_avatar(avatar_file, current_user.username)
        user.avatar_url = avatar_url
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile.",
        )
    db.refresh(user)
    return {"message": "avatar updated successfully."}


async def remove_user_avatar(db: Session, current_user: UserProfileResponse) -> dict:
    user = db.query(User).filter(User.id == current_user.id).first()
    await delete_avatar(user.username)
    user.avatar_url = generate_default_avatar(username=user.username)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user avatar.",
        )

    db.refresh(user)

    return {"message": "avatar deleted successfully."}


def generate_default_avatar(username: str) -> str:

    encoded_name = quote(username)
    return f"https://ui-avatars.com/api/?name={encoded_name}&size=200&background=random&color=fff&bold=true"


async def deactivate_user_account(
    db: Session, current_user: UserProfileResponse
) -> dict:
    user = db.query(User).filter(User.id == current_user.id).first()
    user.is_active = False
    try:
        db.query(RefreshToken).filter((RefreshToken.user_id == current_user.id) & (RefreshToken.is_revoked == False)).update({"is_revoked": True})
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate user account.",
        )
    
    keys = redis_client.keys("leaderboard:*")
    for key in keys:
        redis_client.zrem(key, str(current_user.id))
  
    return {"message": "account deactivated successfully."}


def reactivate_account(email: str, password: str, db: Session) -> dict:
    user = db.query(User).filter(User.email == email.lower().strip()).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with this email.",
        )
    if user.is_active:
        return {"message": "Account is already active."}
    if not auth.verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid password.",
        )
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email before reactivating your account.",
        )
    user.is_active = True
    try:
        db.commit()
        db.refresh(user)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reactivate account.",
        )

    token = auth.generate_token(user.id, user.username)
    refresh_token = auth.generate_refresh_token(user.id)
    return {"message": "Account reactivated successfully.", "token": token,"refresh_token": refresh_token}

async def delete_user_account(db: Session, current_user: UserProfileResponse) -> dict:
    user = db.query(User).filter(User.id == current_user.id).first()

    try:
        db.delete(user)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user account.",
        )
    keys = redis_client.keys("leaderboard:*")
    for key in keys:
        redis_client.zrem(key, str(current_user.id))

    return {"message": "account deleted successfully."}

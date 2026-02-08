from typing import Optional
from config.cloudinary import upload_avatar
from config.db import get_db
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from models.response import UserProfileResponse
from models.tables import User
from fastapi import UploadFile, File
from sqlalchemy.orm import Session


security = HTTPBearer()


def get_current_user(
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
    return UserProfileResponse(
        id=payload["user_id"],
        username=payload["username"],
        avatar_url=user.avatar_url if user.avatar_url else None,
    )


async def update_user_profile(
    db: Session,
    current_user: UserProfileResponse,
    avatar_file: Optional[UploadFile] = File(None, description="Avatar image file"),
) -> UserProfileResponse:

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

    return UserProfileResponse(
        id=user.id,
        username=user.username,
        avatar_url=user.avatar_url if user.avatar_url else None,
    )


def generate_default_avatar(username: str) -> str:
    from urllib.parse import quote

    encoded_name = quote(username)
    return f"https://ui-avatars.com/api/?name={encoded_name}&size=200&background=random&color=fff&bold=true"

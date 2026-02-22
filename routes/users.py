from fastapi import APIRouter, Depends
from controllers import users
from config.db import get_db
from models.response import DifferentUserProfileResponse, UserProfileResponse
from sqlalchemy.orm import Session
from fastapi import UploadFile, File


router = APIRouter(
    prefix="/users",
)


@router.get("/api/profile")
async def get_profile(
    current_user: dict = Depends(users.get_current_user),
) -> UserProfileResponse:
    return current_user


@router.get("/api/profile/{username}")
async def get_user_profile(
    username: str, db: Session = Depends(get_db)
) -> DifferentUserProfileResponse:
    """View another user's public profile"""
    return await users.get_user_profile(username=username, db=db)


@router.put("/api/profile")
async def update_profile(
    avatar_file: UploadFile,
    db: Session = Depends(get_db),
    current_user: dict = Depends(users.get_current_user),
) -> dict:

    return await users.update_user_profile(db, current_user, avatar_file)


@router.delete("/api/profile/avatar")
async def delete_avatar(
    db: Session = Depends(get_db),
    current_user: dict = Depends(users.get_current_user),
) -> dict:
    """Remove custom avatar and revert to default"""
    return await users.remove_user_avatar(db, current_user)

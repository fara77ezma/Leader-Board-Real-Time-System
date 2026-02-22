from fastapi import APIRouter, Depends
from controllers import users
from config.db import get_db
from models.response import UserProfileResponse
from sqlalchemy.orm import Session
from fastapi import UploadFile, File
from typing import Optional


router = APIRouter(
    prefix="/users",
)


@router.get("/api/profile")
async def get_profile(
    current_user: dict = Depends(users.get_current_user),
) -> UserProfileResponse:
    return current_user


@router.put("/api/profile")
async def update_profile(
    avatar_file: Optional[UploadFile] = File(None, description="Avatar image file"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(users.get_current_user),
) -> UserProfileResponse:

    return await users.update_user_profile(db, current_user, avatar_file)

from fastapi import APIRouter, Depends
from fastapi import Request
from controllers import users
from config.db import get_db
from models.response import DifferentUserProfileResponse, UserProfileResponse
from sqlalchemy.orm import Session
from fastapi import UploadFile


router = APIRouter(
    prefix="/users",
)


@router.get("/api/profile")
async def get_my_profile(
    request: Request,
    db: Session = Depends(get_db),
) -> UserProfileResponse:

    return await users.get_current_user(request=request, db=db)


@router.get("/api/profile/{username}")
async def get_user_profile(
    username: str, db: Session = Depends(get_db)
) -> DifferentUserProfileResponse:
    """View another user's public profile"""
    return await users.get_user_profile(username=username, db=db)


@router.put("/api/profile")
async def update_profile(
    request: Request,
    avatar_file: UploadFile,
    db: Session = Depends(get_db),
) -> dict:
    current_user = await users.get_current_user(request=request, db=db)
    return await users.update_user_profile(db, current_user, avatar_file)


@router.delete("/api/profile/avatar")
async def delete_avatar(
    request: Request,
    db: Session = Depends(get_db),
) -> dict:
    """Remove custom avatar and revert to default"""
    current_user = await users.get_current_user(request=request, db=db)
    return await users.remove_user_avatar(db, current_user)

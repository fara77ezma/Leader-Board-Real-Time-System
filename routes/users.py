from fastapi import APIRouter, Depends, Request, UploadFile
from controllers import auth, users
from config.db import get_db
from models.response import DifferentUserProfileResponse, UserProfileResponse
from sqlalchemy.orm import Session
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi_limiter.depends import RateLimiter


security = HTTPBearer()


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get("/api/profile")
async def get_my_profile(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UserProfileResponse:

    return await users.get_current_user(credentials=credentials, db=db)


@router.get("/api/profile/{username}")
async def get_user_profile(
    username: str, db: Session = Depends(get_db)
) -> DifferentUserProfileResponse:
    """View another user's public profile"""
    return await users.get_user_profile(username=username, db=db)


@router.put("/api/profile")
async def update_avatar(
    avatar_file: UploadFile,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> dict:
    current_user = await users.get_current_user(credentials=credentials, db=db)
    return await users.update_user_avatar(db, current_user, avatar_file)


@router.put("/api/profile/deactivate")
async def deactivate_account(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    current_user = await users.get_current_user(credentials=credentials, db=db)
    return await users.deactivate_user_account(db, current_user)

@router.post(
    "/reactivate-account",
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
)
def reactivate_account(
    email: str,
    password: str,
    db: Session = Depends(get_db),
):
    return users.reactivate_account(email, password, db)

@router.delete("/api/profile/avatar")
async def delete_avatar(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    current_user = await users.get_current_user(credentials=credentials, db=db)
    return await users.remove_user_avatar(db, current_user)


@router.delete("/api/profile")
async def delete_account(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    current_user = await users.get_current_user(credentials=credentials, db=db)
    return await users.delete_user_account(db, current_user)

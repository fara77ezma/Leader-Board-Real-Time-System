from pydantic import BaseModel
from datetime import datetime


class RegisterResponse(BaseModel):
    message: str
    username: str
    requires_verification: bool


class UserProfileResponse(BaseModel):
    id: int
    username: str
    avatar_url: str
    # Leaderboard stats
    games: dict[str, dict] = {}
    # Metadata
    is_verified: bool = False
    created_at: datetime


class DifferentUserProfileResponse(BaseModel):
    username: str
    avatar_url: str
    # Leaderboard stats
    games: dict[str, dict] = {}

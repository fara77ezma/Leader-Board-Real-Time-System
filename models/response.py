from pydantic import BaseModel
from fastapi import UploadFile


class RegisterResponse(BaseModel):
    message: str
    username: str
    requires_verification: bool


class UserProfileResponse(BaseModel):
    id: int
    username: str
    avatar_url: UploadFile = None

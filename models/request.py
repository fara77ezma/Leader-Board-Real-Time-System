from pydantic import BaseModel, EmailStr, Field, model_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    phone_number: str = Field(..., pattern=r"^01[0-9]{9}$")
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class SubmitScoreRequest(BaseModel):
    game_id: str
    score: int

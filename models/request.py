import re
from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(
        ...,
        min_length=3,
        max_length=20,
    )
    phone_number: str
    password: str

    @field_validator("username")
    # classmethod because the validator needs to access the class itself with cls because its run before instantiating the class
    @classmethod
    def validate_username(cls, v: str):
        if not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_]+$", v):
            raise ValueError(
                "Username must start with a letter and contain only letters, numbers, and underscores"
            )
        return v

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: str):
        if not re.fullmatch(r"^01[0125][0-9]{8}$", v):
            raise ValueError(
                "Phone number must start with 010, 011, 012, or 015 and be followed by 8 digits"
            )
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v


class LoginRequest(BaseModel):
    username: str
    password: str


class SubmitScoreRequest(BaseModel):
    game_id: str
    score: int

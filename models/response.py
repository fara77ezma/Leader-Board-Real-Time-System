from pydantic import BaseModel


class RegisterResponse(BaseModel):
    message: str
    username: str
    requires_verification: bool

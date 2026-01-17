from pydantic import BaseModel


class RegisterResponse(BaseModel):
    message: str
    user_name: str

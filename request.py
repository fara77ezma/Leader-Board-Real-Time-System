from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str 
    phone_number: str  = Field(..., pattern=r'^01[0-9]{9}$')
    password: str

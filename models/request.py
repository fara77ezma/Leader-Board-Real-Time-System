from pydantic import BaseModel, EmailStr, Field,model_validator

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str 
    phone_number: str  = Field(..., pattern=r'^01[0-9]{9}$')
    password: str

class LoginRequest(BaseModel):
    email: EmailStr | None = None
    username: str | None = None
    password: str
    @model_validator(mode="after")
    def check_identifier(self):
        if not self.email and not self.username:
            raise ValueError("Either email or username must be provided.")
        return self
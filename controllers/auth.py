import os
import uuid
from models.request import LoginRequest, RegisterRequest
from models.tables import User
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from fastapi import Depends
from fastapi.security import HTTPBearer



pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")



def register_user(request: RegisterRequest,db: Session) -> dict:
    # Check if email or username already exists
    existing_user = db.query(User).filter(
        (User.email == request.email) | (User.username == request.username)
    ).first()

    if existing_user:
        return {"error": "Email or username already exists."}


    new_user = User(
        user_code=str(uuid.uuid4()),
        email=request.email,
        username=request.username,
        phone_number=request.phone_number,
        password_hash=hash_password(request.password),
    )
    db.add(new_user)
    try:
        db.commit()
    except Exception as e:
        print("Error during user registration:", e)
        db.rollback()
        return {"error": "Registration failed."}
    
    return {"message": "User registered successfully."}


def login_user(request: LoginRequest,db: Session):
    existing_user = db.query(User).filter(
       User.username == request.username
    ).first()

    if not existing_user:
        return {"error": "Invalid username."}
    if not verify_password(request.password, existing_user.password_hash):
        return {"error": "Incorrect password."}
    token = create_token(existing_user.id, existing_user.username)
    return {"message": "Login successful.", "token": token}


def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_token(user_id: int, username: str):
    """Create a simple JWT token"""
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)  
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print("Decoded JWT payload:", payload)
        return payload
    except jwt.ExpiredSignatureError:
        return {"error": "Token has expired."}
    except jwt.InvalidTokenError:
        return {"error": "Invalid token."}
    
from sqlite3 import IntegrityError
from fastapi import status, HTTPException
import os
import uuid
from models.request import LoginRequest, RegisterRequest
from models.response import RegisterResponse
from models.tables import User
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# deprecated="auto" ensures compatibility with older hashes
# bcrypt__rounds=12 sets the cost factor for bcrypt the more rounds, the more secure but slower
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")


def register_user(
    request: RegisterRequest, db: Session, client_ip: str
) -> RegisterResponse:

    # Check if email or username or phone number already exists
    existing_user = (
        db.query(User)
        .filter(
            (User.email == request.email)
            | (User.username == request.username)
            | (User.phone_number == request.phone_number)
        )
        .first()
    )
    # If any of them exist, raise a conflict error
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with these credentials already exists",
        )

    # Create new user
    new_user = User(
        user_code=str(uuid.uuid4()),
        email=request.email,
        username=request.username,
        phone_number=request.phone_number,
        password_hash=hash_password(request.password),
    )

    try:
        # Add and commit the new user to the database
        db.add(new_user)

        db.commit()

        # reload the instance from the database to get any defaults set by the DB
        db.refresh(new_user)

        return RegisterResponse(
            message="User registered successfully.",
            user_name=new_user.username,
        )
    except IntegrityError as e:
        db.rollback()
        # This catches database constraint violations
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with these credentials already exists",
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again",
        )


def login_user(request: LoginRequest, db: Session):
    existing_user = db.query(User).filter(User.username == request.username).first()

    if not existing_user:
        return {"error": "Invalid username."}
    if not verify_password(request.password, existing_user.password_hash):
        return {"error": "Incorrect password."}
    token = create_token(existing_user.id, existing_user.username)
    return {"message": "Login successful.", "token": token}


def hash_password(password: str) -> str:
    # Hash the password using Passlib
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_token(user_id: int, username: str):
    """Create a simple JWT token"""
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
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

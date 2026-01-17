import secrets
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
from pydantic import EmailStr
from config.mail import fast_mail
from fastapi_mail import MessageType, MessageSchema, ConnectionConfig

# deprecated="auto" ensures compatibility with older hashes
# bcrypt__rounds=12 sets the cost factor for bcrypt the more rounds, the more secure but slower
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")


def register_user(
    request: RegisterRequest, db: Session, client_ip: str
) -> RegisterResponse:

    print(f"Registration attempt from IP: {client_ip}")
    # Normalize input data
    # emails are case-insensitive
    email = request.email.lower().strip()
    username = request.username.strip()
    phone_number = request.phone_number.strip()

    # Check if email or username or phone number already exists
    existing_user = (
        db.query(User)
        .filter(
            (User.email == email)
            | (User.username == username)
            | (User.phone_number == phone_number)
        )
        .first()
    )
    # If any of them exist, raise a conflict error
    if existing_user:
        if existing_user.email == email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists",
            )
        elif existing_user.username == username:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this username already exists",
            )
        elif existing_user.phone_number == phone_number:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this phone number already exists",
            )

    verification_code = secrets.token_urlsafe(32)
    verification_expiry = datetime.now(timezone.utc) + timedelta(hours=1)

    try:
        password_hash = hash_password(request.password)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again",
        )
    # Create new user
    new_user = User(
        user_code=str(uuid.uuid4()),
        email=email,
        username=username,
        phone_number=phone_number,
        password_hash=password_hash,
        email_verification_code=verification_code,
        email_verification_expiry=verification_expiry,
    )

    try:
        # Add and commit the new user to the database
        db.add(new_user)

        db.commit()

        # reload the instance from the database to get any defaults set by the DB
        db.refresh(new_user)

        print(
            "User registered successfully.",
            f"user_name : {new_user.username}, email: {new_user.email}",
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
    try:
        email_sent = send_verification_email(
            email=new_user.email,
            username=new_user.username,
            verification_code=new_user.email_verification_code,
        )
        if email_sent:
            print(f"Verification email sent successfully to {email}")
        else:
            print(f"Failed to send verification email to {email}")
    except Exception as e:
        print(f"Error sending verification email: {e}")
        email_sent = False

    return RegisterResponse(
        message="Registration successful. Please check your email to verify your account.",
        requires_verification=True,
        username=new_user.username,
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


async def send_verification_email(
    email: EmailStr, username: str, verification_code: str
) -> bool:
    base_url = os.getenv("BASE_URL", "http://localhost:5000")
    verification_url = f"{base_url}/auth/verify-email?code={verification_code}"

    # Prepare email content

    html_content, text_content = generate_email_content(username, verification_url)
    message = MessageSchema(
        subject="Verify Your Email Address",
        recipients=[email],
        body=text_content,
        subtype=MessageType.html,
        html=html_content,
    )

    try:
        await fast_mail.send_message(message)
        print(f"Verification email sent to {email}")
        return True
    except Exception as e:
        print(f"Failed to send verification email to {email}: {e}")
        return False


def generate_email_content(username, verification_url):
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Welcome {username}! 🎉</h2>
            <p>Thank you for registering. Please verify your email address by clicking the button below:</p>
            <p style="margin: 30px 0;">
                <a href="{verification_url}" 
                   style="background-color: #4CAF50; 
                          color: white; 
                          padding: 12px 30px; 
                          text-decoration: none; 
                          border-radius: 5px;
                          display: inline-block;">
                    Verify Email Address
                </a>
            </p>
            <p style="color: #666;">
                Or copy and paste this link into your browser:<br>
                <a href="{verification_url}">{verification_url}</a>
            </p>
            <p style="color: #999; font-size: 12px;">
                This link will expire in 24 hours.
            </p>
        </body>
    </html>
    """

    # Plain text version
    text_content = f"""
    Welcome {username}!
    Thank you for registering. Please verify your email by clicking this link:
    {verification_url}
    This link expires in 24 hours.
    """
    return html_content, text_content

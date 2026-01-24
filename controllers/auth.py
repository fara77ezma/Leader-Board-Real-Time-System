import secrets
import re
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
from fastapi_mail import MessageType, MessageSchema

# deprecated="auto" ensures compatibility with older hashes
# bcrypt__rounds=12 sets the cost factor for bcrypt the more rounds, the more secure but slower
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")


async def register_user(
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
        email_sent = await send_verification_email(
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


def login_user(request: LoginRequest, db: Session) -> dict:
    existing_user = db.query(User).filter(User.username == request.username).first()

    if not existing_user:
        return {"error": "Invalid username."}
    if not verify_password(request.password, existing_user.password_hash):
        return {"error": "Incorrect password."}
    if not existing_user.is_verified:
        return {
            "error": "Email not verified. Please verify your email before logging in."
        }
    token = create_token(existing_user.id, existing_user.username)
    return {"message": "Login successful.", "token": token}


def hash_password(password: str) -> str:
    # Hash the password using Passlib
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_token(user_id: int, username: str) -> str:
    """Create a simple JWT token"""
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


def verify_token(token: str) -> dict:
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
    message = build_email_structure(
        email,
        username,
        subject="Email Verification",
        url_path="verify-email",
        verification_code=verification_code,
    )
    print("fast_mail:", fast_mail, " sending to:", email, "message:", message)

    try:
        await fast_mail.send_message(message)
        print(f"Verification email sent to {email}")
        return True
    except Exception as e:
        print(f"Failed to send verification email to {email}: {e}")
        return False


def build_email_structure(
    email: EmailStr, username: str, subject: str, url_path: str, verification_code: str
) -> MessageSchema:
    base_url = os.getenv("BASE_URL", "http://localhost:5000")
    verification_url = f"{base_url}/auth/{url_path}?code={verification_code}"

    # Prepare email content
    if url_path == "verify-email":
        text_content = generate_verification_email_content(username, verification_url)
    else:
        text_content = generate_password_reset_email_content(username, verification_url)
    message = MessageSchema(
        subject=subject,
        recipients=[email],
        body=text_content,
        subtype=MessageType.plain,
    )

    return message


def generate_verification_email_content(username: str, verification_url: str) -> str:

    # Plain text version
    text_content = f"""
                    ╔═══════════════════════════════════════════════════════╗
                    ║                                                        ║
                    ║          Welcome to Our Platform, {username}!         ║
                    ║                                                        ║
                    ╚═══════════════════════════════════════════════════════╝

                Thank you for registering! 🎉

                To complete your registration, please verify your email address 
                by clicking the link below:

                🔗 Verification Link:
                {verification_url}

                ⏰ Important: This link will expire in 24 hours.

            If you didn't create an account, you can safely ignore this email.

        ---
        Need help? Contact our support team.
    """
    return text_content


def email_verification(code: str, db: Session) -> dict:
    # check if code exists
    user = db.query(User).filter(User.email_verification_code == code).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code.",
        )
    # check if already verified
    if user.is_verified:
        return {"message": "Email is already verified."}

    expiration_time = (user.email_verification_expiry).replace(tzinfo=timezone.utc)
    # check if code is expired
    if expiration_time < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code has expired.",
        )

    user.is_verified = True
    user.email_verification_code = None
    user.email_verification_expiry = None
    try:
        db.commit()
        db.refresh(user)
        return {"message": "Email verified successfully."}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify email.",
        )


async def resend_verification(email: str, db: Session, client_ip: str) -> dict:
    print(f"Resend verification attempt from IP: {client_ip} for email: {email}")
    user = db.query(User).filter(User.email == email.lower().strip()).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with this email.",
        )
    if user.is_verified:
        return {"message": "Email is already verified."}

    verification_code = secrets.token_urlsafe(32)
    verification_expiry = datetime.now(timezone.utc) + timedelta(hours=1)

    user.email_verification_code = verification_code
    user.email_verification_expiry = verification_expiry

    try:
        db.commit()
        db.refresh(user)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resend verification email.",
        )

    try:
        email_sent = await send_verification_email(
            email=user.email,
            username=user.username,
            verification_code=user.email_verification_code,
        )
        if email_sent:
            print(f"Verification email resent successfully to {email}")
            return {"message": "Verification email resent successfully."}
        else:
            print(f"Failed to resend verification email to {email}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to resend verification email.",
            )
    except Exception as e:
        print(f"Error resending verification email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resend verification email.",
        )


async def forgot_password(email: str, db: Session, client_ip: str) -> dict:
    print(f"Forgot password attempt from IP: {client_ip} for email: {email}")

    user = db.query(User).filter(User.email == email.lower().strip()).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with this email.",
        )
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email is not verified. Please verify your email first.",
        )
    # Here you would generate a password reset token and send it via email
    verification_code = secrets.token_urlsafe(32)
    user.password_reset_code = verification_code
    user.password_reset_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
    try:
        db.commit()
        db.refresh(user)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate password reset.",
        )
    # Send password reset email
    message = build_email_structure(
        email=user.email,
        username=user.username,
        subject="Password Reset Request",
        url_path="reset-password",
        verification_code=user.password_reset_code,
    )
    try:
        await fast_mail.send_message(message)
        print(f"Password reset email sent to {email}")
        return {"message": "Password reset email sent successfully."}
    except Exception as e:
        print(f"Failed to send password reset email to {email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send password reset email.",
        )


def generate_password_reset_email_content(username: str, verification_url: str) -> str:
    text_content = f"""
                    ╔═══════════════════════════════════════════════════════╗
                    ║                                                        ║
                    ║          Password Reset Request for {username}         ║
                    ║                                                        ║
                    ╚═══════════════════════════════════════════════════════╝   
                We received a request to reset your password.
                To reset your password, click the link below:
                🔗 Password Reset Link:
                {verification_url}
                ⏰ Important: This link will expire in 1 hour.
                If you didn't request a password reset, you can safely ignore this email.
                ---
                Need help? Contact our support team.
                """
    return text_content


def reset_password(code: str, new_password: str, db: Session) -> dict:
    user = db.query(User).filter(User.password_reset_code == code).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid password reset code.",
        )
    expiration_time = (user.password_reset_expiry).replace(tzinfo=timezone.utc)

    if expiration_time < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset code has expired.",
        )
    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 8 characters long.",
        )
    if not re.search(r"[A-Z]", new_password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must contain at least one uppercase letter.",
        )
    if not re.search(r"[a-z]", new_password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must contain at least one lowercase letter.",
        )
    if not re.search(r"[0-9]", new_password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must contain at least one digit.",
        )
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", new_password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must contain at least one special character.",
        )

    user.password_hash = hash_password(new_password)
    user.password_reset_code = None
    user.password_reset_expiry = None
    try:
        db.commit()
        db.refresh(user)
        return {"message": "Password reset successfully."}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password.",
        )

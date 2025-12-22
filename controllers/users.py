import hashlib
import uuid
from models.request import LoginRequest, RegisterRequest
from models.tables import User
from sqlalchemy.orm import Session
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

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
        (User.email == request.email) | (User.username == request.username)
    ).first()
    if not existing_user and request.email:
        return {"error": "Invalid email."}
    if not existing_user and request.username:
        return {"error": "Invalid username."}
    if not verify_password(request.password, existing_user.password_hash):
        return {"error": "Incorrect password."}
    return {"message": "Login successful."}
    




def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

import hashlib
import uuid
from request import RegisterRequest
from db.tables import User
from sqlalchemy.orm import Session


def register_user(request: RegisterRequest,db: Session) -> dict:
    
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


def hash_password(pwd):
    pwd_bytes = pwd.encode('utf-8')
    hashed_pwd = hashlib.sha256(pwd_bytes).hexdigest()
    return hashed_pwd
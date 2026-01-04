from fastapi import APIRouter, Depends
from db.db import get_db
from sqlalchemy.orm import Session
from models.request import LoginRequest, RegisterRequest
from controllers.auth import login_user, register_user


router = APIRouter(
    prefix="/auth",
)

@router.post("/register")
def register(
    request: RegisterRequest, db: Session = Depends(get_db)
):
   return register_user(request, db)

@router.post("/login")
def login(
    request: LoginRequest, db: Session = Depends(get_db)
):
   return login_user(request, db)

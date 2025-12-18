from fastapi import APIRouter, Depends
from db.db import get_db
from sqlalchemy.orm import Session
from request import RegisterRequest
from controllers.users import register_user

router = APIRouter(
    prefix="/users",
)

@router.post("/register")
def register(
    request: RegisterRequest, db: Session = Depends(get_db)
):
   return register_user(request, db)
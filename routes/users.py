from fastapi import APIRouter, Depends
from controllers.users import get_current_user

router = APIRouter(
    prefix="/users",
)

@router.get("/api/profile")
def get_profile(current_user: dict = Depends(get_current_user)):
    return current_user

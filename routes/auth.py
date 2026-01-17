from fastapi import APIRouter, Depends
from db.db import get_db
from sqlalchemy.orm import Session
from models.request import LoginRequest, RegisterRequest
from controllers.auth import login_user, register_user
from fastapi_limiter.depends import RateLimiter
from fastapi import status, Request


router = APIRouter(
    prefix="/auth",
)


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
)
def register(
    request: Request,
    request_data: RegisterRequest,
    db: Session = Depends(get_db),
):
    client_ip = request.client.host
    return register_user(
        request=request_data,
        db=db,
        client_ip=client_ip,
    )


@router.post("/login", dependencies=[Depends(RateLimiter(times=5, seconds=60))])
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    return login_user(request, db)

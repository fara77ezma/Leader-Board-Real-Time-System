from controllers import auth
from fastapi import APIRouter, Depends
from config.db import get_db
from sqlalchemy.orm import Session
from models.request import LoginRequest, RegisterRequest
from models.response import RegisterResponse
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
async def register(
    request: Request,
    request_data: RegisterRequest,
    db: Session = Depends(get_db),
) -> RegisterResponse:
    client_ip = request.client.host
    return await auth.register_user(
        request=request_data,
        db=db,
        client_ip=client_ip,
    )


@router.post("/login", dependencies=[Depends(RateLimiter(times=5, seconds=60))])
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    return auth.login_user(request, db)


@router.get("/verify-email")
def verify_email(code: str, db: Session = Depends(get_db)):
    return auth.email_verification(code, db)


@router.post(
    "/resend-verification", dependencies=[Depends(RateLimiter(times=3, seconds=60))]
)
async def resend_verification_email(
    request: Request,
    email: str,
    db: Session = Depends(get_db),
):
    client_ip = request.client.host
    return await auth.resend_verification(email, db, client_ip)


@router.post(
    "/forgot-password", dependencies=[Depends(RateLimiter(times=3, seconds=60))]
)
async def forgot_password(
    request: Request,
    email: str,
    db: Session = Depends(get_db),
):
    client_ip = request.client.host
    return await auth.forgot_password(email, db, client_ip)


@router.post(
    "/reset-password", dependencies=[Depends(RateLimiter(times=5, seconds=60))]
)
def reset_password(
    code: str,
    new_password: str,
    db: Session = Depends(get_db),
):
    return auth.reset_password(code, new_password, db)

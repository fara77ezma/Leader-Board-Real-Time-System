from fastapi.security import HTTPAuthorizationCredentials,HTTPBearer
from controllers import auth
from fastapi import APIRouter, Depends, status, Request
from config.db import get_db
from sqlalchemy.orm import Session
from models.request import LoginRequest, RefreshTokenRequest, RegisterRequest
from models.response import RegisterResponse
from fastapi_limiter.depends import RateLimiter

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

security = HTTPBearer()

@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    # allow 5 request per 5 seconds from the same IP
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
)
async def register(
    request_data: RegisterRequest,
    db: Session = Depends(get_db),
) -> RegisterResponse:
    return await auth.register_user(
        request=request_data,
        db=db,
    )


@router.post(
    "/login",
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    return auth.login_user(request, db)


@router.get("/verify-email")
def verify_email(code: str, db: Session = Depends(get_db)):
    return auth.email_verification(code, db)


@router.post(
    "/resend-verification",
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
)
async def resend_verification_email(
    email: str,
    db: Session = Depends(get_db),
):
    return await auth.resend_verification(email, db)


@router.post(
    "/forgot-password",
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
)
async def forgot_password(
    email: str,
    db: Session = Depends(get_db),
):
    return await auth.forgot_password(email, db)


@router.post(
    "/reset-password",
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
)
def reset_password(
    code: str,
    new_password: str,
    db: Session = Depends(get_db),
):
    return auth.reset_password(code, new_password, db)

@router.post("/logout")
def logout(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    return auth.revoke_refresh_token(db = db , refresh_token= request.refresh_token)

@router.post("/refresh-token")
def refresh_access_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    return auth.refresh_access_token(refresh_token = request.refresh_token, db =db )

@router.get("/delete-expired-tokens")
async def delete_expired_tokens(db: Session = Depends(get_db), credentials: HTTPAuthorizationCredentials = Depends(security)):
    await auth.require_admin(db=db,credentials=credentials)
    return auth.delete_expired_refresh_tokens(db)
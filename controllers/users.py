from fastapi import Depends
from fastapi.security import HTTPBearer
from controllers.auth import verify_token

security = HTTPBearer()


def get_current_user(token: str = Depends(security)):
    payload = verify_token(token.credentials)
    if "error" in payload:
        return {"error": payload["error"]}
    return {"user_id": payload["user_id"], "username": payload["username"]}

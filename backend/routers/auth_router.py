from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel
from backend.auth import authenticate_user, create_access_token, Token
from backend.audit import log_action
from backend.config import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login", response_model=Token)
def login(body: LoginRequest, request: Request):
    user = authenticate_user(body.username, body.password)
    if not user:
        log_action(body.username, "LOGIN", "System", ip_address=request.client.host, details="FAILED login attempt")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(user["username"], user["role"])
    log_action(body.username, "LOGIN", "System", ip_address=request.client.host, details="Successful login")
    return Token(access_token=token, expires_in=settings.jwt_access_token_expire_minutes * 60)

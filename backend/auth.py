"""
HIPAA-compliant JWT authentication for FastAPI.
All endpoints that touch PHI require a valid Bearer token.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from backend.config import get_settings

settings = get_settings()
bearer_scheme = HTTPBearer()

# In production replace with a proper user store (Airtable Users table / external IdP)
DEMO_USERS = {
    "admin": {"password": "zentox-admin-2024!", "role": "admin"},
    "staff": {"password": "zentox-staff-2024!", "role": "staff"},
}


class TokenData(BaseModel):
    username: str
    role: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


def create_access_token(username: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload = {"sub": username, "role": role, "exp": expire, "iat": datetime.now(timezone.utc)}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> TokenData:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return TokenData(username=payload["sub"], role=payload["role"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def require_admin(token: TokenData = Depends(verify_token)) -> TokenData:
    if token.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return token


def authenticate_user(username: str, password: str) -> Optional[dict]:
    user = DEMO_USERS.get(username)
    if user and user["password"] == password:
        return {"username": username, "role": user["role"]}
    return None

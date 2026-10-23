from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import (
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
)
from app.database import get_db
from app.models.user import User
from app.schemas.common import AuthResponse, StatusMessage

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()


def normalize_phone(raw_phone: str) -> str:
    return raw_phone.strip().replace(" ", "").lstrip("+")


def create_access_token(subject: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expires_at}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    print(f"Decoding token: {token}")
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from exc

    phone = payload.get("sub")
    if phone is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing subject")

    user = db.query(User).filter(User.phone == normalize_phone(str(phone))).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if (current_user.role or "").strip().lower() not in {"officer", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user

class LoginPyload(BaseModel):
    phone: str
    pin: str


@router.post("/login", response_model=AuthResponse)
def login(login_payload: LoginPyload, db: Session = Depends(get_db)) -> AuthResponse:
    user = db.query(User).filter(User.phone == login_payload.phone).first()
    print(f"Attempting login for phone: {login_payload.phone}, user found: {user}")
    if user and user.pin != login_payload.pin:
        raise HTTPException(status_code=401, detail="Incorrect phone or pin.")
    if user is None:
        raise HTTPException(status_code=401, detail="Incorrect phone or pin.")
    token = create_access_token(login_payload.phone)
    return AuthResponse(
        success=True,
        message="Login successful",
        token=token,
        expires_in=JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me")
def get_current_profile( credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        print(f"Decoded payload: {payload}")
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from exc
    phone = payload.get("sub")
    if phone is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing subject")
    user = db.query(User).filter(User.phone == normalize_phone(str(phone))).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return {
        "id": user.id,
        "name": user.name,
        "phone": user.phone,
        "email": user.email,
        "role": user.role,
    }

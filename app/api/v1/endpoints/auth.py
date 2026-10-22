from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import (
    DEMO_OFFICER_PHONE,
    DEMO_OFFICER_PIN,
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


@router.post("/login", response_model=AuthResponse)
def login(phone: str, pin: str, db: Session = Depends(get_db)) -> AuthResponse:
    normalized_phone = normalize_phone(phone)
    expected_phone = normalize_phone(DEMO_OFFICER_PHONE)

    if normalized_phone != expected_phone or pin != DEMO_OFFICER_PIN:
        raise HTTPException(status_code=401, detail="Incorrect phone number or PIN.")

    user = db.query(User).filter(User.phone == normalized_phone).first()
    if user is None:
        user = User(
            name="Admin Officer",
            phone=normalized_phone,
            national_id="00000000",
            email="officer@cbk.go.ke",
            role="Officer",
            active=True,
            pin=DEMO_OFFICER_PIN,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token(normalized_phone)
    return AuthResponse(
        success=True,
        message="Login successful",
        token=token,
        expires_in=JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me")
def get_current_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "phone": current_user.phone,
        "email": current_user.email,
        "role": current_user.role,
    }

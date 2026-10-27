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
from app.models.user_account_restriction import UserAccountRestriction
from app.schemas.common import AuthResponse, StatusMessage
from app.services.activity_log_service import record_activity

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()


def normalize_phone(raw_phone: str) -> str:
    digits = (raw_phone or "").strip().replace(" ", "").replace("-", "").lstrip("+")
    if not digits:
        return ""
    if digits.startswith("254") and len(digits) == 12:
        return digits
    if digits.startswith("0") and len(digits) == 10:
        return "254" + digits[1:]
    if len(digits) == 9 and digits[0] in "71":
        return "254" + digits
    if digits.startswith("254") and len(digits) == 13:
        return digits
    return digits


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
    normalized_phone = normalize_phone(login_payload.phone)
    user = db.query(User).filter(User.phone == normalized_phone).first()
    print(f"Attempting login for phone: {normalized_phone}, user found: {user}")

    restriction = db.query(UserAccountRestriction).filter(UserAccountRestriction.user_id == user.id).first() if user else None

    if user and user.pin != login_payload.pin:
        if restriction is not None:
            restriction.failed_login_attempts = (restriction.failed_login_attempts or 0) + 1
            db.commit()
        record_activity(
            db,
            user,
            action="login_failed",
            entity_type="auth",
            description=f"{user.name} failed portal login with a wrong PIN.",
        )
        raise HTTPException(status_code=401, detail="Incorrect phone or pin.")
    if user is None:
        raise HTTPException(status_code=401, detail="Incorrect phone or pin.")

    if restriction is not None:
        if restriction.failed_login_attempts >= restriction.failed_login_threshold:
            reason = restriction.reason or "Account locked due to too many failed login attempts."
            record_activity(
                db,
                user,
                action="login_failed",
                entity_type="auth",
                description=f"{user.name} failed portal login: {reason}",
            )
            raise HTTPException(status_code=403, detail=reason)

    if not user.active:
        record_activity(
            db,
            user,
            action="login_failed",
            entity_type="auth",
            description=f"{user.name} failed portal login because the account is inactive.",
        )
        raise HTTPException(status_code=403, detail="Account is inactive.")
    if restriction and not restriction.can_portal_login:
        reason = restriction.reason or "Portal login is restricted by an officer."
        record_activity(
            db,
            user,
            action="login_failed",
            entity_type="auth",
            description=f"{user.name} failed portal login: {reason}",
        )
        raise HTTPException(status_code=403, detail=reason)

    if restriction is not None:
        restriction.failed_login_attempts = 0
        db.commit()

    token = create_access_token(normalized_phone)
    record_activity(
        db,
        user,
        action="login",
        entity_type="auth",
        description=f"{user.name} signed in to the portal.",
    )
    return AuthResponse(
        success=True,
        message="Login successful",
        token=token,
        expires_in=JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    token = create_access_token(normalized_phone)
    record_activity(
        db,
        user,
        action="login",
        entity_type="auth",
        description=f"{user.name} signed in to the portal.",
    )
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

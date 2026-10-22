from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.common import SecurityCreate
from app.services.security_service import SecurityService

router = APIRouter(prefix="/securities", tags=["securities"])


@router.get("")
def list_securities(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    del current_user
    return SecurityService(db).list_securities()


@router.get("/{security_id}")
def get_security(
    security_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    del current_user
    return SecurityService(db).get_security(security_id)


@router.post("")
def create_security(
    payload: SecurityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    del current_user
    return SecurityService(db).create_security(payload.model_dump())


@router.put("/{security_id}")
def update_security(
    security_id: int,
    payload: SecurityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    del current_user
    return SecurityService(db).update_security(security_id, payload.model_dump())


@router.patch("/{security_id}/toggle")
def toggle_security(
    security_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    del current_user
    return SecurityService(db).toggle_security(security_id)

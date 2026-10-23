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
    page: int = 1,
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    del current_user
    items = SecurityService(db).list_securities()
    page = max(1, page)
    limit = max(1, min(limit, 100))
    total = len(items)
    offset = (page - 1) * limit
    paged_items = items[offset:offset + limit]
    return {
        "items": paged_items,
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": max(1, (total + limit - 1) // limit) if total else 1,
        "has_next": offset + limit < total,
        "has_prev": page > 1,
    }


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

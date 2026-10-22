from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user, require_admin
from app.database import get_db
from app.models.user import User
from app.schemas.common import StatusMessage, UserCreate, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("")
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    del current_user
    return UserService(db).list_users()


@router.get("/{user_id}")
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    del current_user
    return UserService(db).get_user(user_id)


@router.post("", response_model=StatusMessage)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> StatusMessage:
    del current_user
    try:
        user = UserService(db).create_user(payload.model_dump())
    except HTTPException:
        raise
    return StatusMessage(success=True, message=f"User '{user.name}' created successfully")


@router.put("/{user_id}")
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    del current_user
    return UserService(db).update_user(user_id, payload.model_dump(exclude_unset=True))


@router.patch("/{user_id}/toggle")
def toggle_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    del current_user
    return UserService(db).deactivate_user(user_id)


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    del current_user
    return UserService(db).delete_user(user_id)

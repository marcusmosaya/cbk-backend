from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user, require_admin
from app.database import get_db
from app.models.user import User
from app.models.user_account_restriction import UserAccountRestriction
from app.schemas.common import StatusMessage, UserAccountRestrictionUpdate, UserCreate, UserUpdate
from app.services.activity_log_service import record_activity
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("")
def list_users(
    page: int = 1,
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    del current_user
    items = UserService(db).list_users()
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
    try:
        user = UserService(db).create_user(payload.model_dump())
    except HTTPException:
        raise
    record_activity(
        db,
        current_user,
        action="create",
        entity_type="user",
        entity_id=user.id,
        description=f"Created user {user.name}.",
    )
    return StatusMessage(success=True, message=f"User '{user.name}' created successfully")


@router.put("/{user_id}")
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    updated = UserService(db).update_user(user_id, payload.model_dump(exclude_unset=True))
    record_activity(
        db,
        current_user,
        action="update",
        entity_type="user",
        entity_id=user_id,
        description=f"Updated user profile for user ID {user_id}.",
    )
    return updated


@router.patch("/{user_id}/toggle")
def toggle_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    updated = UserService(db).deactivate_user(user_id)
    record_activity(
        db,
        current_user,
        action="toggle",
        entity_type="user",
        entity_id=user_id,
        description=f"Toggled account status for user ID {user_id}.",
    )
    return updated


@router.get("/{user_id}/restrictions")
def get_user_restrictions(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    del current_user
    restriction = db.query(UserAccountRestriction).filter(UserAccountRestriction.user_id == user_id).first()
    if restriction is None:
        return {"user_id": user_id, "can_login": True, "can_withdraw": True, "reason": None}
    return {
        "user_id": user_id,
        "can_login": restriction.can_login,
        "can_withdraw": restriction.can_withdraw,
        "reason": restriction.reason,
    }


@router.put("/{user_id}/restrictions")
def update_user_restrictions(
    user_id: int,
    payload: UserAccountRestrictionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    user = UserService(db).get_user(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    restriction = db.query(UserAccountRestriction).filter(UserAccountRestriction.user_id == user_id).first()
    if restriction is None:
        restriction = UserAccountRestriction(
            user_id=user_id,
            can_login=payload.can_login,
            can_withdraw=payload.can_withdraw,
            reason=payload.reason or "Account restricted by officer.",
        )
        db.add(restriction)
    else:
        restriction.can_login = payload.can_login
        restriction.can_withdraw = payload.can_withdraw
        restriction.reason = payload.reason or restriction.reason or "Account restricted by officer."

    db.commit()
    db.refresh(restriction)
    record_activity(
        db,
        current_user,
        action="restrict",
        entity_type="user_restriction",
        entity_id=user_id,
        description=f"Updated account restrictions for user ID {user_id}: login={restriction.can_login}, withdraw={restriction.can_withdraw}.",
    )
    return {
        "user_id": user_id,
        "can_login": restriction.can_login,
        "can_withdraw": restriction.can_withdraw,
        "reason": restriction.reason,
    }


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    deleted = UserService(db).delete_user(user_id)
    record_activity(
        db,
        current_user,
        action="delete",
        entity_type="user",
        entity_id=user_id,
        description=f"Deleted user ID {user_id}.",
    )
    return deleted

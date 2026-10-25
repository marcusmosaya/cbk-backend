from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import require_admin
from app.database import get_db, get_or_create_system_account
from app.models.user import User
from app.models.user_activity_log import UserActivityLog

router = APIRouter(prefix="/activity-logs", tags=["activity-logs"])


@router.get("")
def list_activity_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    del current_user
    system_account = get_or_create_system_account(db)
    query = db.query(UserActivityLog).join(User, UserActivityLog.user_id == User.id, isouter=True).filter(
        UserActivityLog.user_id != system_account.id
    )

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                User.name.ilike(term),
                UserActivityLog.action.ilike(term),
                UserActivityLog.entity_type.ilike(term),
                UserActivityLog.description.ilike(term),
            )
        )

    total = query.count()
    rows = query.order_by(UserActivityLog.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    return {
        "items": [
            {
                "id": row.id,
                "user_id": row.user_id,
                "user_name": row.user.name if row.user else "Unknown user",
                "action": row.action,
                "entity_type": row.entity_type,
                "entity_id": row.entity_id,
                "description": row.description,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ],
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": max(1, (total + limit - 1) // limit) if total else 1,
        "has_next": page * limit < total,
        "has_prev": page > 1,
    }

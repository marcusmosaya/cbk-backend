from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.user_activity_log import UserActivityLog


def record_activity(
    db: Session,
    user: User | None,
    action: str,
    entity_type: str,
    entity_id: int | None = None,
    description: str | None = None,
):
    if user is None:
        return None

    entry = UserActivityLog(
        user_id=user.id,
        action=(action or "update").strip()[:64],
        entity_type=(entity_type or "portal").strip()[:64],
        entity_id=entity_id,
        description=(description or f"{user.name} performed {action or 'update'}").strip()[:500],
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

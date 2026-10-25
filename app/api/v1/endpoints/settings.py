from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.common import SystemSettingsUpdate
from app.services.activity_log_service import record_activity
from app.services.settings_service import SettingsService

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("")
def get_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    del current_user
    return SettingsService(db).get_settings()


@router.put("")
def update_settings(
    payload: SystemSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    updated = SettingsService(db).update_settings(payload.model_dump())
    record_activity(
        db,
        current_user,
        action="update",
        entity_type="system_setting",
        description=f"Updated system settings: inactivity_days={payload.inactivity_days}, run_hour={payload.run_hour}, run_minute={payload.run_minute}.",
    )
    return updated

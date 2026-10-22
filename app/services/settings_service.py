from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.settings_repository import SettingsRepository


class SettingsService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = SettingsRepository(db)

    def get_settings(self):
        settings = self.repository.get()
        if settings is None:
            raise HTTPException(status_code=404, detail="Settings not found")
        return settings

    def update_settings(self, data: dict):
        settings = self.repository.get()
        if settings is None:
            return self.repository.create(data)
        return self.repository.update(settings, data)

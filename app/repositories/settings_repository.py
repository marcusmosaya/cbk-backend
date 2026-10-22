from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.system_setting import SystemSetting


class SettingsRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self) -> SystemSetting | None:
        return self.db.query(SystemSetting).first()

    def create(self, data: dict) -> SystemSetting:
        setting = SystemSetting(**data)
        self.db.add(setting)
        self.db.commit()
        self.db.refresh(setting)
        return setting

    def update(self, setting: SystemSetting, data: dict) -> SystemSetting:
        for field, value in data.items():
            if value is not None:
                setattr(setting, field, value)
        self.db.commit()
        self.db.refresh(setting)
        return setting

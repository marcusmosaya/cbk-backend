from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.security_repository import SecurityRepository


class SecurityService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = SecurityRepository(db)

    def list_securities(self):
        return self.repository.get_all()

    def get_security(self, security_id: int):
        security = self.repository.get_by_id(security_id)
        if security is None:
            raise HTTPException(status_code=404, detail="Security not found")
        return security

    def create_security(self, data: dict):
        return self.repository.create(data)

    def update_security(self, security_id: int, data: dict):
        security = self.get_security(security_id)
        return self.repository.update(security, data)

    def toggle_security(self, security_id: int):
        security = self.get_security(security_id)
        return self.repository.update(security, {"is_active": not security.is_active})

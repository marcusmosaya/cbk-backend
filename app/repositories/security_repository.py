from __future__ import annotations

from typing import Sequence

from sqlalchemy.orm import Session

from app.models.security import Security


class SecurityRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> Sequence[Security]:
        return self.db.query(Security).order_by(Security.id).all()

    def get_by_id(self, security_id: int) -> Security | None:
        return self.db.query(Security).filter(Security.id == security_id).first()

    def create(self, data: dict) -> Security:
        security = Security(**data)
        self.db.add(security)
        self.db.commit()
        self.db.refresh(security)
        return security

    def update(self, security: Security, data: dict) -> Security:
        for field, value in data.items():
            if value is not None:
                setattr(security, field, value)
        self.db.commit()
        self.db.refresh(security)
        return security

    def delete(self, security: Security) -> None:
        self.db.delete(security)
        self.db.commit()

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Sequence

from sqlalchemy.orm import Session

from app.models.ussd_log import UssdLog
from app.models.ussd_menu import UssdMenu
from app.models.ussd_session import UssdSession


class UssdRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_sessions(self) -> Sequence[UssdSession]:
        return self.db.query(UssdSession).order_by(UssdSession.updated_at.desc()).all()

    def get_session_by_id(self, session_id: str) -> UssdSession | None:
        return self.db.query(UssdSession).filter(UssdSession.session_id == session_id).first()

    def get_active_session_by_phone(self, phone: str) -> UssdSession | None:
        return (
            self.db.query(UssdSession)
            .filter(UssdSession.phone == phone, UssdSession.is_active.is_(True))
            .order_by(UssdSession.updated_at.desc())
            .first()
        )

    def create_session(self, phone: str, session_id: str, state: str = "start", menu_code: str | None = None) -> UssdSession:
        session = UssdSession(
            session_id=session_id,
            phone=phone,
            state=state,
            menu_code=menu_code,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def update_session(self, session: UssdSession, **kwargs) -> UssdSession:
        for field, value in kwargs.items():
            if value is not None:
                setattr(session, field, value)
        session.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_menus(self) -> Sequence[UssdMenu]:
        return self.db.query(UssdMenu).order_by(UssdMenu.sequence.asc(), UssdMenu.id.asc()).all()

    def get_menu_by_code(self, code: str) -> UssdMenu | None:
        return self.db.query(UssdMenu).filter(UssdMenu.code == code, UssdMenu.is_active.is_(True)).first()

    def create_menu(self, data: dict) -> UssdMenu:
        menu = UssdMenu(**data)
        self.db.add(menu)
        self.db.commit()
        self.db.refresh(menu)
        return menu

    def create_log(
        self,
        phone: str,
        request_data: str | None,
        response_data: str | None,
        session_id: int | None = None,
        request_type: str = "input",
    ) -> UssdLog:
        log = UssdLog(
            session_id=session_id,
            phone=phone,
            request_type=request_type,
            request_data=request_data,
            response_data=response_data,
            created_at=datetime.utcnow(),
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def list_logs(self, session_id: int | None = None) -> Sequence[UssdLog]:
        query = self.db.query(UssdLog)
        if session_id is not None:
            query = query.filter(UssdLog.session_id == session_id)
        return query.order_by(UssdLog.created_at.desc()).all()

    def prune_expired_sessions(self, max_age_minutes: int = 5) -> int:
        cutoff = datetime.utcnow() - timedelta(minutes=max_age_minutes)
        expired = (
            self.db.query(UssdSession)
            .filter(UssdSession.created_at < cutoff, UssdSession.is_active.is_(True))
            .all()
        )
        for session in expired:
            session.is_active = False
        if expired:
            self.db.commit()
        return len(expired)

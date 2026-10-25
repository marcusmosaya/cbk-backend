from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UssdSession(Base):
    __tablename__ = "ussd_sessions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    state: Mapped[str] = mapped_column(String(64), default="start", nullable=False)
    menu_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_input: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    logs = relationship("UssdLog", back_populates="session")

    def __repr__(self) -> str:
        return f"UssdSession(id={self.id}, session_id={self.session_id!r}, phone={self.phone!r}, state={self.state!r})"
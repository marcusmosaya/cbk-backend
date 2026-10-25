from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UssdLog(Base):
    __tablename__ = "ussd_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    session_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("ussd_sessions.id"),
        nullable=True,
        index=True,
    )
    phone: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    request_type: Mapped[str] = mapped_column(String(32), default="input", nullable=False)
    request_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    session = relationship("UssdSession", back_populates="logs")

    def __repr__(self) -> str:
        return f"UssdLog(id={self.id}, phone={self.phone!r}, request_type={self.request_type!r})"
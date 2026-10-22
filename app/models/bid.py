from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Bid(Base):
    __tablename__ = "bids"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    reference: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    instrument_id: Mapped[int | None] = mapped_column(ForeignKey("securities.id"), nullable=True)
    instrument_name: Mapped[str] = mapped_column(String(255), nullable=False)
    bid_type: Mapped[str] = mapped_column(String(64), nullable=False, default="T-Bill")
    bid_amount: Mapped[float] = mapped_column(Float, nullable=False)
    face_value: Mapped[float] = mapped_column(Float, nullable=False)
    rate: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="Pending", nullable=False)
    placed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    security = relationship("Security")

    def __repr__(self) -> str:
        return f"Bid(id={self.id}, reference={self.reference!r}, status={self.status!r})"

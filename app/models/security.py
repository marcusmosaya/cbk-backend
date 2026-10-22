from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean, Date, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Security(Base):
    __tablename__ = "securities"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    instrument_type: Mapped[str] = mapped_column(String(64), nullable=False)
    maturity: Mapped[str] = mapped_column(String(32), nullable=False)
    opening_date: Mapped[date] = mapped_column(Date, nullable=False)
    closing_date: Mapped[date] = mapped_column(Date, nullable=False)
    minimum_bid: Mapped[float] = mapped_column(Float, nullable=False)
    target_amount: Mapped[float] = mapped_column(Float, nullable=False)
    previous_rate: Mapped[str] = mapped_column(String(32), default="N/A", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"Security(id={self.id}, name={self.name!r}, type={self.instrument_type!r})"

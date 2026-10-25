from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserTransaction(Base):
    __tablename__ = "user_transactions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    debit_account_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    credit_account_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    note: Mapped[str] = mapped_column(String(255), default="System transaction", nullable=False)
    reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    user = relationship("User", foreign_keys=[user_id])
    debit_account = relationship("User", foreign_keys=[debit_account_id])
    credit_account = relationship("User", foreign_keys=[credit_account_id])

    def __repr__(self) -> str:
        return f"UserTransaction(user_id={self.user_id}, type={self.type!r}, amount={self.amount})"
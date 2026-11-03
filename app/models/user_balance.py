from __future__ import annotations

from sqlalchemy import BigInteger, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class UserBalance(Base):
    __tablename__ = "user_balances"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    artificial_cash: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    user = relationship("User")

    @property
    def total_amount(self) -> float:
        return float(self.amount) + float(self.artificial_cash)

    def __repr__(self) -> str:
        return (
            f"UserBalance(user_id={self.user_id}, amount={self.amount}, "
            f"artificial_cash={self.artificial_cash})"
        )

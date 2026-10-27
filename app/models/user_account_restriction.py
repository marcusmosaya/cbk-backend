from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserAccountRestriction(Base):
    __tablename__ = "user_account_restrictions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False, unique=True, index=True)

    # Access toggles
    can_login: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    can_withdraw: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    can_deposit: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    can_transfer: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    can_ussd: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    can_portal_login: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Amount limits
    min_deposit: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    max_deposit: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    min_withdraw: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    max_withdraw: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    max_transfer: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Failed login tracking
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_login_threshold: Mapped[int] = mapped_column(Integer, default=5, nullable=False)

    # Per-restriction reasons
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    reason_login: Mapped[str | None] = mapped_column(Text, nullable=True)
    reason_withdraw: Mapped[str | None] = mapped_column(Text, nullable=True)
    reason_deposit: Mapped[str | None] = mapped_column(Text, nullable=True)
    reason_transfer: Mapped[str | None] = mapped_column(Text, nullable=True)
    reason_ussd: Mapped[str | None] = mapped_column(Text, nullable=True)
    reason_portal_login: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user = relationship("User")

    def __repr__(self) -> str:
        return (
            f"UserAccountRestriction(user_id={self.user_id}, "
            f"can_login={self.can_login}, can_withdraw={self.can_withdraw}, "
            f"can_deposit={self.can_deposit}, can_transfer={self.can_transfer})"
        )
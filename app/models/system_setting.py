from __future__ import annotations

from sqlalchemy import Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SystemSetting(Base):
    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    inactivity_days: Mapped[int] = mapped_column(Integer, default=90, nullable=False)
    auto_deactivation_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    run_hour: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    run_minute: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return (
            f"SystemSetting(id={self.id}, inactivity_days={self.inactivity_days}, "
            f"run_hour={self.run_hour}, run_minute={self.run_minute})"
        )

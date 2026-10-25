from __future__ import annotations

from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import DATABASE_URL, DEMO_OFFICER_PHONE, DEMO_OFFICER_PIN

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, future=True, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

SYSTEM_ACCOUNT_NAME = "Pesanexa Main Account"
SYSTEM_ACCOUNT_PHONE = "+000000000000"


def get_or_create_system_account(db):
    from app.models.user import User
    from app.models.user_balance import UserBalance

    system_account = (
        db.query(User)
        .filter(User.name == SYSTEM_ACCOUNT_NAME)
        .first()
    )

    if system_account is not None:
        existing_balance = db.query(UserBalance).filter(UserBalance.user_id == system_account.id).first()
        if existing_balance is None:
            db.add(UserBalance(user_id=system_account.id, amount=0.0))
            db.commit()
        return system_account

    system_account = User(
        name=SYSTEM_ACCOUNT_NAME,
        phone=SYSTEM_ACCOUNT_PHONE,
        national_id="SYSTEM-ACCOUNT",
        email="system@fms.local",
        role="System",
        active=False,
        pin=None,
    )
    db.add(system_account)
    db.flush()
    db.add(UserBalance(user_id=system_account.id, amount=0.0))
    db.commit()
    db.refresh(system_account)
    return system_account


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    from app.models import __all__ as _models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def seed_demo_data(db) -> None:
    from app.models.user import User
    from app.models.user_transaction import UserTransaction
    from app.models.security import Security
    from app.models.system_setting import SystemSetting

    system_account = get_or_create_system_account(db)

    def as_date(value: str) -> date:
        return date.fromisoformat(value)
    if db.query(User).count() == 1:
        db.add_all(
            [
                User(
                    name="Marcus Mosaya",
                    phone=DEMO_OFFICER_PHONE,
                    national_id="445666",
                    email="marcus@gmail.com",
                    role="Officer",
                    active=True,
                    pin=DEMO_OFFICER_PIN,
                    )
                    ]
        )



    if db.query(SystemSetting).count() == 0:
        db.add(
            SystemSetting(
                inactivity_days=90,
                auto_deactivation_enabled=True,
                run_hour=2,
                run_minute=0,
            )
        )

    db.commit()

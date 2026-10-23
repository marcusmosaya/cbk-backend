from __future__ import annotations

from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import DATABASE_URL, DEMO_OFFICER_PHONE, DEMO_OFFICER_PIN

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


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

    def as_date(value: str) -> date:
        return date.fromisoformat(value)
    if db.query(User).count() == 0:
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
                    ),
                User(
                    name="Abdiwahab Abdi",
                    phone="+254727228795",
                    national_id="445666",
                    email="d@gmail.com",
                    role="Investor",
                    active=True,
                    pin="1234",
                ),
                User(
                    name="Andrew Taboi",
                    phone="+254711812832",
                    national_id="5566677",
                    email="t@gmail.com",
                    role="Investor",
                    active=True,
                    pin="1234",
                ),
                User(
                    name="Charles Shidzugane",
                    phone="+254722303157",
                    national_id="3567800",
                    email="gkk@gmail.com",
                    role="Investor",
                    active=False,
                    pin="1234",
                ),
                User(
                    name="Charles Okoo",
                    phone="+254726601415",
                    national_id="566777",
                    email="c@gmail.com",
                    role="Investor",
                    active=True,
                    pin="1234",
                ),
                User(
                    name="David Karuiki",
                    phone="+254722653414",
                    national_id="355557",
                    email="d@gmail.com",
                    role="Investor",
                    active=True,
                    pin="1234",
                ),
            ]
        )

    if db.query(Security).count() == 0:
        db.add_all(
            [
                Security(
                    name="91-Day Treasury Bill",
                    instrument_type="T-Bill",
                    maturity="91d",
                    opening_date=as_date("2026-06-30"),
                    closing_date=as_date("2026-07-07"),
                    minimum_bid=50000,
                    target_amount=5000000000,
                    previous_rate="8.8206",
                    is_active=True,
                ),
                Security(
                    name="182-Day Treasury Bill",
                    instrument_type="T-Bill",
                    maturity="182d",
                    opening_date=as_date("2026-06-30"),
                    closing_date=as_date("2026-07-07"),
                    minimum_bid=50000,
                    target_amount=4000000000,
                    previous_rate="8.7782",
                    is_active=True,
                ),
                Security(
                    name="364-Day Treasury Bill",
                    instrument_type="T-Bill",
                    maturity="364d",
                    opening_date=as_date("2026-06-30"),
                    closing_date=as_date("2026-07-07"),
                    minimum_bid=50000,
                    target_amount=3000000000,
                    previous_rate="8.9746",
                    is_active=True,
                ),
                Security(
                    name="2-Yr Infrastructure Bond",
                    instrument_type="Bond",
                    maturity="730d",
                    opening_date=as_date("2026-06-30"),
                    closing_date=as_date("2026-07-14"),
                    minimum_bid=100000,
                    target_amount=10000000000,
                    previous_rate="N/A",
                    is_active=True,
                ),
                Security(
                    name="5-Yr Infrastructure Bond",
                    instrument_type="Bond",
                    maturity="1825d",
                    opening_date=as_date("2026-06-30"),
                    closing_date=as_date("2026-07-14"),
                    minimum_bid=100000,
                    target_amount=8000000000,
                    previous_rate="N/A",
                    is_active=True,
                ),
                Security(
                    name="10-Yr Government Bond",
                    instrument_type="Bond",
                    maturity="3650d",
                    opening_date=as_date("2026-06-30"),
                    closing_date=as_date("2026-07-14"),
                    minimum_bid=100000,
                    target_amount=15000000000,
                    previous_rate="N/A",
                    is_active=True,
                ),
            ]
        )

    if db.query(UserTransaction).count() == 0:
        users_by_name = {user.name: user for user in db.query(User).all()}
        db.add_all(
            [
                UserTransaction(
                    user_id=users_by_name["Abdiwahab Abdi"].id,
                    debit_account_id=None,
                    credit_account_id=users_by_name["Abdiwahab Abdi"].id,
                    type="credit",
                    amount=250000,
                    note="Account top-up",
                ),
                UserTransaction(
                    user_id=users_by_name["Charles Okoo"].id,
                    debit_account_id=users_by_name["Charles Okoo"].id,
                    credit_account_id=None,
                    type="debit",
                    amount=90000,
                    note="Bid settlement",
                ),
                UserTransaction(
                    user_id=users_by_name["Andrew Taboi"].id,
                    debit_account_id=None,
                    credit_account_id=users_by_name["Andrew Taboi"].id,
                    type="credit",
                    amount=180000,
                    note="Investor funding",
                ),
                UserTransaction(
                    user_id=users_by_name["David Karuiki"].id,
                    debit_account_id=users_by_name["David Karuiki"].id,
                    credit_account_id=None,
                    type="debit",
                    amount=120000,
                    note="Withdrawal",
                ),
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

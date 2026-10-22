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
    from app.models.security import Security
    from app.models.system_setting import SystemSetting

    def as_date(value: str) -> date:
        return date.fromisoformat(value)

    normalized_admin_phone = DEMO_OFFICER_PHONE.strip().replace(" ", "").lstrip("+")
    admin_user = db.query(User).filter(User.phone == normalized_admin_phone).first()
    if admin_user is None:
        admin_user = User(
            name="Admin Officer",
            phone=normalized_admin_phone,
            national_id="00000000",
            email="officer@cbk.go.ke",
            role="Officer",
            active=True,
            pin=DEMO_OFFICER_PIN,
        )
        db.add(admin_user)
    else:
        admin_user.name = "Admin Officer"
        admin_user.national_id = "00000000"
        admin_user.email = "officer@cbk.go.ke"
        admin_user.role = "Officer"
        admin_user.active = True
        admin_user.pin = DEMO_OFFICER_PIN

    if db.query(User).count() == 0:
        db.add_all(
            [
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

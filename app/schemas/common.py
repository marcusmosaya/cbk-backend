from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class StatusMessage(BaseModel):
    success: bool
    message: str


class AuthResponse(StatusMessage):
    token: str
    expires_in: int


class UserCreate(BaseModel):
    name: str = Field(..., min_length=2)
    phone: str
    national_id: str
    email: EmailStr
    role: str = "Investor"
    active: bool = True


class UserUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    national_id: str | None = None
    email: EmailStr | None = None
    role: str | None = None
    active: bool | None = None


class SecurityCreate(BaseModel):
    name: str
    instrument_type: str = "T-Bill"
    maturity: str
    opening_date: str
    closing_date: str
    minimum_bid: float
    target_amount: float
    previous_rate: str | None = None
    is_active: bool = True


class BidCreate(BaseModel):
    phone: str
    instrument_id: int | None = None
    instrument_name: str
    bid_type: str = "T-Bill"
    bid_amount: float
    face_value: float
    rate: str
    status: str = "Pending"


class BalanceTopUp(BaseModel):
    user_id: int
    amount: float = Field(..., gt=0)


class SystemSettingsUpdate(BaseModel):
    inactivity_days: int = Field(..., ge=1, le=3650)
    run_hour: int = Field(..., ge=0, le=23)
    run_minute: int = Field(..., ge=0, le=59)
    auto_deactivation_enabled: bool = True

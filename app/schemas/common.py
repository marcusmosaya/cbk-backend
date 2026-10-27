from __future__ import annotations

from typing import Literal

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
    pin: str = "0000"
    role: Literal["Officer", "Investor"] = "Investor"
    active: bool = True


class UserUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    national_id: str | None = None
    email: EmailStr | None = None
    role: Literal["Officer", "Investor"] | None = None
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
    amount: float
    transaction_type: Literal["credit", "debit"] = "credit"
    note: str | None = None


class SystemAccountAdjustment(BaseModel):
    amount: float
    transaction_type: Literal["credit", "debit"] = "credit"
    note: str | None = None


class UserAccountRestrictionUpdate(BaseModel):
    can_login: bool = True
    can_withdraw: bool = True
    can_deposit: bool = True
    can_transfer: bool = True
    can_ussd: bool = True
    can_portal_login: bool = True
    min_deposit: float = 0.0
    max_deposit: float = 0.0
    min_withdraw: float = 0.0
    max_withdraw: float = 0.0
    max_transfer: float = 0.0
    failed_login_threshold: int = 5
    reason: str | None = None
    reason_login: str | None = None
    reason_withdraw: str | None = None
    reason_deposit: str | None = None
    reason_transfer: str | None = None
    reason_ussd: str | None = None
    reason_portal_login: str | None = None


class SystemSettingsUpdate(BaseModel):
    inactivity_days: int = Field(..., ge=1, le=3650)
    run_hour: int = Field(..., ge=0, le=23)
    run_minute: int = Field(..., ge=0, le=59)
    auto_deactivation_enabled: bool = True


class ActivityLogEntry(BaseModel):
    id: int
    user_id: int
    user_name: str
    action: str
    entity_type: str
    entity_id: int | None = None
    description: str
    created_at: str | None = None


class UssdSessionStart(BaseModel):
    phone: str
    session_id: str | None = None


class UssdInput(BaseModel):
    phone: str
    input: str


class UssdMenuCreate(BaseModel):
    code: str
    title: str
    description: str | None = None
    parent_code: str | None = None
    sequence: int = 1
    is_active: bool = True
    content: str | None = None

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user, require_admin
from app.database import get_db
from app.models.user import User
from app.models.withdrawal_request import WithdrawalRequest
from app.schemas.common import StatusMessage
from app.services.activity_log_service import record_activity
from app.services.withdrawal_service import WithdrawalService

router = APIRouter(prefix="/withdrawals", tags=["withdrawals"])


@router.post("")
def create_withdrawal_request(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    amount = float(payload.get("amount", 0))
    phone = payload.get("phone", current_user.phone)
    service = WithdrawalService(db)
    request = service.create_request(current_user.id, amount, phone)
    record_activity(
        db,
        current_user,
        action="withdrawal_request",
        entity_type="withdrawal_request",
        entity_id=request.id,
        description=f"{current_user.name} requested withdrawal of KES {amount:,.2f}.",
    )
    return {
        "id": request.id,
        "user_id": request.user_id,
        "amount": float(request.amount),
        "phone": request.phone,
        "status": request.status,
        "reference": request.reference,
        "created_at": request.created_at.isoformat() if request.created_at else None,
    }


@router.get("")
def list_withdrawal_requests(
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = WithdrawalService(db)
    requests = service.list_requests(status=status)
    return [
        {
            "id": r.id,
            "user_id": r.user_id,
            "amount": float(r.amount),
            "phone": r.phone,
            "status": r.status,
            "reference": r.reference,
            "officer_note": r.officer_note,
            "denial_reason": r.denial_reason,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in requests
    ]


@router.post("/{request_id}/approve")
def approve_withdrawal(
    request_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    note = payload.get("note")
    service = WithdrawalService(db)
    result = service.approve(request_id, current_user.id, note=note)
    record_activity(
        db,
        current_user,
        action="withdrawal_approve",
        entity_type="withdrawal_request",
        entity_id=request_id,
        description=f"{current_user.name} approved withdrawal request {request_id}.",
    )
    return {"success": True, "request_id": request_id, **result}


@router.post("/{request_id}/deny")
def deny_withdrawal(
    request_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    reason = payload.get("reason", "No reason provided")
    service = WithdrawalService(db)
    result = service.deny(request_id, current_user.id, reason=reason)
    record_activity(
        db,
        current_user,
        action="withdrawal_deny",
        entity_type="withdrawal_request",
        entity_id=request_id,
        description=f"{current_user.name} denied withdrawal request {request_id}: {reason}",
    )
    return {"success": True, "request_id": request_id, **result}


@router.post("/deposit/initiate")
def initiate_deposit(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    amount = float(payload.get("amount", 0))
    phone = payload.get("phone", current_user.phone)
    service = WithdrawalService(db)
    result = service.process_stk_deposit(current_user.id, phone, amount)
    record_activity(
        db,
        current_user,
        action="deposit_initiate",
        entity_type="daraja_stk",
        entity_id=None,
        description=f"{current_user.name} initiated M-Pesa deposit of KES {amount:,.2f}.",
    )
    return result


@router.get("/deposits")
def list_deposits(
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = WithdrawalService(db)
    is_officer = (current_user.role or "").strip().lower() in {"officer", "admin"}
    user_id = None if is_officer else current_user.id
    deposits = service.list_deposits(user_id=user_id, status=status)
    return deposits
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.pending_deposit import PendingDeposit
from app.models.user import User
from app.models.user_transaction import UserTransaction
from app.models.withdrawal_request import WithdrawalRequest
from app.repositories.balance_repository import BalanceRepository
from app.repositories.transaction_repository import TransactionRepository
from app.services.email_service import EmailService

router = APIRouter(prefix="/daraja/callback", tags=["daraja-callback"])


def _process_stk_callback(db: Session, body: dict) -> dict:
    """Handle STK Push callback from Safaricom."""
    checkout_request_id = body.get("CheckoutRequestID")
    result_code = str(body.get("ResultCode", "1"))

    if not checkout_request_id:
        raise HTTPException(status_code=400, detail="Missing CheckoutRequestID")

    # Try USSD deposit first
    pending = (
        db.query(PendingDeposit)
        .filter(PendingDeposit.checkout_request_id == checkout_request_id)
        .order_by(PendingDeposit.created_at.desc())
        .first()
    )

    if pending is not None:
        pending.daraja_response = json.dumps(body)
        if result_code == "0":
            pending.status = "approved"
            balance_repo = BalanceRepository(db)
            balance_repo.adjust(pending.user_id, pending.amount, "credit")
            tx_repo = TransactionRepository(db)
            tx_repo.create(
                user_id=pending.user_id,
                transaction_type="credit",
                amount=pending.amount,
                note=f"M-Pesa deposit confirmed via Daraja. Ref: {pending.reference}",
                credit_account_id=pending.user_id,
                debit_account_id=None,
                reference=f"DEP-CONFIRMED-{pending.id}",
            )
            user = db.query(User).filter(User.id == pending.user_id).first()
            if user and user.email:
                EmailService.send_deposit_confirmation(
                    user.email, pending.amount, pending.reference
                )
        else:
            pending.status = "failed"
        db.commit()
        return {"success": True, "status": pending.status, "source": "ussd_deposit"}

    # Fall back to portal deposit (WithdrawalRequest)
    request = (
        db.query(WithdrawalRequest)
        .filter(WithdrawalRequest.daraja_response.contains(checkout_request_id))
        .order_by(WithdrawalRequest.created_at.desc())
        .first()
    )

    if request is None:
        return {"success": True, "message": "No matching request found"}

    request.daraja_response = json.dumps(body)

    if result_code == "0":
        request.status = "approved"
        balance_repo = BalanceRepository(db)
        balance_repo.adjust(request.user_id, request.amount, "credit")
        tx_repo = TransactionRepository(db)
        tx_repo.create(
            user_id=request.user_id,
            transaction_type="credit",
            amount=request.amount,
            note=f"M-Pesa deposit confirmed via Daraja. Ref: {request.reference}",
            credit_account_id=request.user_id,
            debit_account_id=None,
            reference=f"DEP-CONFIRMED-{request.id}",
        )
        user = db.query(User).filter(User.id == request.user_id).first()
        if user and user.email:
            EmailService.send_deposit_confirmation(
                user.email, request.amount, request.reference or f"DEP-{request.id}"
            )
    else:
        request.status = "failed"

    db.commit()
    return {"success": True, "status": request.status, "source": "portal_deposit"}


def _process_b2c_callback(db: Session, body: dict) -> dict:
    """Handle B2C payout callback from Safaricom."""
    originator_conversation_id = body.get("OriginatorConversationID")
    result_code = str(body.get("ResultCode", "1"))
    result_desc = body.get("ResultDesc", "")

    if not originator_conversation_id:
        raise HTTPException(status_code=400, detail="Missing OriginatorConversationID")

    request = (
        db.query(WithdrawalRequest)
        .filter(WithdrawalRequest.daraja_response.contains(originator_conversation_id))
        .order_by(WithdrawalRequest.created_at.desc())
        .first()
    )

    if request is None:
        return {"success": True, "message": "No matching request found"}

    request.daraja_response = json.dumps(body)

    if result_code == "0":
        request.status = "approved"
    else:
        request.status = "failed"
        request.denial_reason = result_desc or "M-Pesa payout failed"

    db.commit()
    return {"success": True, "status": request.status}


@router.post("/stk")
async def stk_callback(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    return _process_stk_callback(db, body)


@router.post("/b2c")
async def b2c_callback(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    return _process_b2c_callback(db, body)
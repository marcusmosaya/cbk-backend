from __future__ import annotations

import json
import os
import uuid
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.withdrawal_request import WithdrawalRequest
from app.models.user import User
from app.services.daraja_service import DarajaService
from app.services.email_service import EmailService


class WithdrawalService:
    def __init__(self, db: Session):
        self.db = db

    def create_request(self, user_id: int, amount: float, phone: str) -> WithdrawalRequest:
        user = self.db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        if amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be greater than zero")

        reference = f"WDR-{user_id}-{uuid.uuid4().hex[:8].upper()}"
        request = WithdrawalRequest(
            user_id=user_id,
            amount=float(amount),
            phone=phone,
            status="pending",
            reference=reference,
        )
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        return request

    def list_requests(self, status: str | None = None) -> list[WithdrawalRequest]:
        query = self.db.query(WithdrawalRequest)
        if status:
            query = query.filter(WithdrawalRequest.status == status)
        return query.order_by(WithdrawalRequest.created_at.desc()).all()

    def get_request(self, request_id: int) -> WithdrawalRequest:
        request = self.db.query(WithdrawalRequest).filter(WithdrawalRequest.id == request_id).first()
        if request is None:
            raise HTTPException(status_code=404, detail="Withdrawal request not found")
        return request

    def approve(self, request_id: int, officer_id: int, note: str | None = None) -> dict:
        request = self.get_request(request_id)
        if request.status != "pending":
            raise HTTPException(status_code=400, detail="Request already processed")

        daraja = DarajaService()
        token = daraja.get_access_token()
        if not token.get("success"):
            request.status = "failed"
            request.daraja_response = json.dumps(token)
            self.db.commit()
            raise HTTPException(status_code=502, detail="Daraja authentication failed")

        payout = daraja.b2c_payout(
            phone=request.phone,
            amount=request.amount,
            remarks=note or f"Withdrawal for user {request.user_id}",
            access_token=token.get("access_token"),
        )
        request.daraja_response = json.dumps(payout)
        request.officer_note = note

        if payout.get("ResponseCode") == "0":
            request.status = "approved"
            self.db.commit()
            return {"success": True, "status": "approved", "daraja": payout}
        else:
            request.status = "failed"
            self.db.commit()
            return {"success": False, "status": "failed", "daraja": payout}

    def deny(self, request_id: int, officer_id: int, reason: str | None = None) -> dict:
        request = self.get_request(request_id)
        if request.status != "pending":
            raise HTTPException(status_code=400, detail="Request already processed")

        request.status = "denied"
        request.denial_reason = reason or "Withdrawal denied by officer"
        request.officer_note = reason
        self.db.commit()

        user = self.db.query(User).filter(User.id == request.user_id).first()
        if user and user.email:
            EmailService.send_withdrawal_denial(user.email, request.amount, reason or "No reason provided")

        return {"success": True, "status": "denied", "reason": request.denial_reason}

    def process_stk_deposit(self, user_id: int, phone: str, amount: float) -> dict:
        """Initiate an M-Pesa STK Push for a deposit."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        daraja = DarajaService()
        token = daraja.get_access_token()
        if not token.get("success"):
            raise HTTPException(status_code=502, detail="Daraja authentication failed")

        reference = f"DEP-{user_id}-{uuid.uuid4().hex[:8].upper()}"
        response = daraja.stk_push(
            phone=phone,
            amount=amount,
            account_reference=reference,
            transaction_desc=f"Deposit for {user.name}",
            access_token=token.get("access_token"),
        )
        return {
            "reference": reference,
            "checkout_request_id": response.get("CheckoutRequestID"),
            "merchant_request_id": response.get("MerchantRequestID"),
            "response": response,
        }
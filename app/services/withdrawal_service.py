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
        """Initiate an M-Pesa STK Push for a deposit.

        The credited account is always the user whose phone number is being
        used for the STK Push, not necessarily the caller's own account.
        """
        caller = self.db.query(User).filter(User.id == user_id).first()
        if caller is None:
            raise HTTPException(status_code=404, detail="User not found")

        # Find the user whose phone matches the STK Push phone
        normalized_phone = self._normalize_phone(phone)
        target_user = self.db.query(User).filter(User.phone == normalized_phone).first()
        credited_user_id = target_user.id if target_user else user_id

        daraja = DarajaService()

        token = daraja.get_access_token()
        if not token.get("success"):
            raise HTTPException(status_code=502, detail="Daraja authentication failed")

        reference = f"DEP-{credited_user_id}-{uuid.uuid4().hex[:8].upper()}"
        target_name = target_user.name if target_user else caller.name
        response = daraja.stk_push(
            phone=phone,
            amount=amount,
            account_reference=reference,
            transaction_desc=f"Deposit for {target_name}",
            access_token=token.get("access_token"),
        )

        from app.models.deposit_request import DepositRequest
        checkout_request_id = response.get("CheckoutRequestID", "")
        merchant_request_id = response.get("MerchantRequestID", "")

        deposit = DepositRequest(
            user_id=user_id,
            credited_user_id=credited_user_id,
            amount=amount,
            phone=phone,
            source="portal",
            checkout_request_id=checkout_request_id,
            merchant_request_id=merchant_request_id,
            reference=reference,
            status="pending",
            daraja_response=str(response),
        )
        self.db.add(deposit)
        self.db.commit()
        self.db.refresh(deposit)

        return {
            "deposit_id": deposit.id,
            "reference": reference,
            "checkout_request_id": checkout_request_id,
            "merchant_request_id": merchant_request_id,
            "credited_user_id": credited_user_id,
            "response": response,
        }

    def list_deposits(self, user_id: int | None = None, status: str | None = None) -> list:
        """List deposits (portal + ussd), optionally filtered by credited user and/or status."""
        from app.models.deposit_request import DepositRequest
        from app.models.pending_deposit import PendingDeposit

        portal_query = self.db.query(DepositRequest)
        ussd_query = self.db.query(PendingDeposit)

        if user_id is not None:
            portal_query = portal_query.filter(DepositRequest.credited_user_id == user_id)
            ussd_query = ussd_query.filter(PendingDeposit.user_id == user_id)
        if status:
            portal_query = portal_query.filter(DepositRequest.status == status)
            ussd_query = ussd_query.filter(PendingDeposit.status == status)

        portal_deposits = portal_query.order_by(DepositRequest.created_at.desc()).all()
        ussd_deposits = ussd_query.order_by(PendingDeposit.created_at.desc()).all()

        # Normalize to a common shape for the API
        result = []
        for d in portal_deposits:
            result.append({
                "id": d.id,
                "user_id": d.user_id,
                "credited_user_id": d.credited_user_id,
                "amount": float(d.amount),
                "phone": d.phone,
                "source": d.source,
                "status": d.status,
                "reference": d.reference,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            })
        for d in ussd_deposits:
            result.append({
                "id": d.id,
                "user_id": d.user_id,
                "credited_user_id": d.user_id,
                "amount": float(d.amount),
                "phone": d.phone,
                "source": "ussd",
                "status": d.status,
                "reference": d.reference,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            })
        # Sort by created_at desc
        result.sort(key=lambda x: x["created_at"] or "", reverse=True)
        return result
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import BalanceTopUp
from app.services.balance_service import BalanceService

router = APIRouter(prefix="/balances", tags=["balances"])


@router.get("/{user_id}")
def get_user_balance(user_id: int, db: Session = Depends(get_db)):
    balance = BalanceService(db).repository.get_for_user(user_id)
    return {"user_id": user_id, "amount": float(balance.amount if balance else 0.0)}


@router.post("")
def update_balance(payload: BalanceTopUp, db: Session = Depends(get_db)):
    balance = BalanceService(db).top_up(
        payload.user_id,
        payload.amount,
        transaction_type=payload.transaction_type,
        note=payload.note,
    )
    return {"user_id": balance.user_id, "amount": float(balance.amount), "success": True}

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user, require_admin
from app.database import get_db, get_or_create_system_account
from app.models.user import User
from app.schemas.common import BalanceTopUp, SystemAccountAdjustment
from app.services.activity_log_service import record_activity
from app.services.balance_service import BalanceService

router = APIRouter(prefix="/balances", tags=["balances"])


@router.get("/system-account")
def get_system_account_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    del current_user
    system_account = get_or_create_system_account(db)
    from app.models.user_transaction import UserTransaction

    ledger_total = 0.0
    for tx in db.query(UserTransaction).filter(
        UserTransaction.user_id == system_account.id
    ).all():
        if tx.debit_account_id == system_account.id:
            ledger_total += float(tx.amount)
        if tx.credit_account_id == system_account.id:
            ledger_total -= float(tx.amount)

    return {
        "user_id": system_account.id,
        "name": system_account.name,
        "amount": float(ledger_total),
        "source": "ledger",
    }


@router.post("/system-account")
def adjust_system_account_balance(
    payload: SystemAccountAdjustment,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    system_account = get_or_create_system_account(db)
    balance = BalanceService(db).adjust_balance(
        system_account.id,
        payload.amount,
        transaction_type=payload.transaction_type,
        balance_type=payload.balance_type,
        note=payload.note or "Officer system account adjustment",
    )
    record_activity(
        db,
        current_user,
        action="system_account_adjustment",
        entity_type="system_account",
        entity_id=system_account.id,
        description=f"{current_user.name} {'credited' if payload.transaction_type == 'credit' else 'debited'} the company system account by {payload.amount} to the {payload.balance_type} bucket.",
    )
    return {
        "user_id": balance.user_id,
        "name": system_account.name,
        "amount": float(balance.amount),
        "artificial_cash": float(balance.artificial_cash),
        "total_amount": float(balance.total_amount),
        "success": True,
    }


@router.get("/{user_id}")
def get_user_balance(user_id: int, db: Session = Depends(get_db)):
    balance = BalanceService(db).repository.get_for_user(user_id)
    real_amount = float(balance.amount if balance else 0.0)
    artificial_cash = float(balance.artificial_cash if balance else 0.0)
    return {
        "user_id": user_id,
        "amount": real_amount,
        "artificial_cash": artificial_cash,
        "total_amount": real_amount + artificial_cash,
    }


@router.post("")
def update_balance(
    payload: BalanceTopUp,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.balance_type == "artificial" and (current_user.role or "").strip().lower() not in {"officer", "admin"}:
        raise HTTPException(status_code=403, detail="Only officers can add artificial balance.")

    balance = BalanceService(db).top_up(
        payload.user_id,
        payload.amount,
        transaction_type=payload.transaction_type,
        note=payload.note,
        balance_type=payload.balance_type,
    )
    record_activity(
        db,
        current_user,
        action="wallet_update",
        entity_type="balance",
        entity_id=payload.user_id,
        description=f"Updated {payload.balance_type} wallet balance for user ID {payload.user_id} by {payload.amount} ({payload.transaction_type}).",
    )
    return {
        "user_id": balance.user_id,
        "amount": float(balance.amount),
        "artificial_cash": float(balance.artificial_cash),
        "total_amount": float(balance.total_amount),
        "success": True,
    }

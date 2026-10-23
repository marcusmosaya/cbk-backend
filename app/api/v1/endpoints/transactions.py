from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.transaction_repository import TransactionRepository

router = APIRouter(prefix="/transactions", tags=["transactions"])


class TransactionCreate(BaseModel):
    user_id: int
    type: str
    amount: float
    note: str | None = None
    debit_account_id: int | None = None
    credit_account_id: int | None = None
    reference: str | None = None


@router.get("")
def list_transactions(
    page: int = 1,
    limit: int = 5,
    db: Session = Depends(get_db),
):
    transactions = TransactionRepository(db).get_all()
    page = max(1, page)
    limit = max(1, min(limit, 100))
    total = len(transactions)
    offset = (page - 1) * limit
    paged_transactions = transactions[offset:offset + limit]
    return {
        "items": [
            {
                "id": tx.id,
                "user_id": tx.user_id,
                "type": TransactionRepository.normalize_type(tx.type, tx.debit_account_id, tx.credit_account_id),
                "amount": float(tx.amount),
                "note": tx.note,
                "reference": tx.reference,
                "debit_account_id": tx.debit_account_id,
                "credit_account_id": tx.credit_account_id,
                "debit_account_name": tx.debit_account.name if tx.debit_account else None,
                "credit_account_name": tx.credit_account.name if tx.credit_account else None,
                "user_name": tx.user.name if tx.user else "Unknown",
                "date": tx.created_at.isoformat(),
            }
            for tx in paged_transactions
        ],
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": max(1, (total + limit - 1) // limit) if total else 1,
        "has_next": offset + limit < total,
        "has_prev": page > 1,
    }


@router.post("")
def create_transaction(payload: TransactionCreate, db: Session = Depends(get_db)):
    transaction = TransactionRepository(db).create(
        user_id=payload.user_id,
        transaction_type=payload.type,
        amount=payload.amount,
        note=payload.note or "System transaction",
        debit_account_id=payload.debit_account_id,
        credit_account_id=payload.credit_account_id,
        reference=payload.reference,
    )
    return {
        "id": transaction.id,
        "user_id": transaction.user_id,
        "type": transaction.type,
        "amount": float(transaction.amount),
        "note": transaction.note,
        "reference": transaction.reference,
        "debit_account_id": transaction.debit_account_id,
        "credit_account_id": transaction.credit_account_id,
        "debit_account_name": transaction.debit_account.name if transaction.debit_account else None,
        "credit_account_name": transaction.credit_account.name if transaction.credit_account else None,
        "date": transaction.created_at.isoformat(),
        "success": True,
    }

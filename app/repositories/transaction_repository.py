from __future__ import annotations

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.user_transaction import UserTransaction


class TransactionRepository:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def normalize_type(transaction_type: str | None, debit_account_id: int | None = None, credit_account_id: int | None = None) -> str:
        raw = (transaction_type or "").strip().lower()
        if debit_account_id is not None and credit_account_id is None:
            return "debit"
        if credit_account_id is not None and debit_account_id is None:
            return "credit"
        if raw in {"credit", "deposit", "credited", "incoming"}:
            return "credit"
        if raw in {"debit", "withdrawal", "withdrawn", "outgoing", "transfer", "transfer_out"}:
            return "debit"
        return "debit" if raw else "debit"

    def get_all(self):
        return self.db.query(UserTransaction).order_by(desc(UserTransaction.created_at)).all()

    def create(
        self,
        user_id: int,
        transaction_type: str,
        amount: float,
        note: str,
        debit_account_id: int | None = None,
        credit_account_id: int | None = None,
        reference: str | None = None,
    ) -> UserTransaction:
        normalized_type = self.normalize_type(transaction_type, debit_account_id, credit_account_id)
        transaction = UserTransaction(
            user_id=user_id,
            debit_account_id=debit_account_id,
            credit_account_id=credit_account_id,
            type=normalized_type,
            amount=float(amount),
            note=note or "System transaction",
            reference=reference,
        )
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.database import get_or_create_system_account
from app.repositories.balance_repository import BalanceRepository
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.user_repository import UserRepository


class BalanceService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = BalanceRepository(db)
        self.transaction_repository = TransactionRepository(db)
        self.user_repository = UserRepository(db)

    def get_balances(self):
        return self.repository.get_all()

    def adjust_balance(self, user_id: int, amount: float, transaction_type: str = "credit", note: str | None = None):
        if self.user_repository.get_by_id(user_id) is None:
            raise HTTPException(status_code=404, detail="User not found")

        normalized_type = str(transaction_type).lower()
        system_account = get_or_create_system_account(self.db)

        current_balance = self.repository.get_for_user(user_id)
        delta = abs(float(amount)) if normalized_type == "credit" else -abs(float(amount))
        if current_balance is not None and current_balance.amount + delta < 0:
            raise HTTPException(status_code=400, detail="Insufficient balance for debit transaction")

        balance = self.repository.adjust(user_id, amount, normalized_type)
        self.repository.adjust(system_account.id, amount, normalized_type)

        if normalized_type == "credit":
            self.transaction_repository.create(
                user_id=user_id,
                transaction_type=normalized_type,
                amount=abs(float(amount)),
                note=(note or "Deposit") + " | Bank debit: cash increases | Customer deposit liability: increases",
                debit_account_id=system_account.id,
                credit_account_id=user_id,
                reference=f"{normalized_type.upper()}-{user_id}",
            )
        else:
            self.transaction_repository.create(
                user_id=user_id,
                transaction_type=normalized_type,
                amount=abs(float(amount)),
                note=(note or "Withdrawal") + " | Bank credit: cash decreases | Customer deposit liability: decreases",
                debit_account_id=user_id,
                credit_account_id=system_account.id,
                reference=f"{normalized_type.upper()}-{user_id}",
            )
        return balance

    def top_up(self, user_id: int, amount: float, transaction_type: str = "credit", note: str | None = None):
        return self.adjust_balance(user_id, amount, transaction_type, note)

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.user_balance import UserBalance


class BalanceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_for_user(self, user_id: int) -> UserBalance | None:
        return self.db.query(UserBalance).filter(UserBalance.user_id == user_id).first()

    def adjust(self, user_id: int, amount: float, transaction_type: str = "credit") -> UserBalance:
        balance = self.get_for_user(user_id)
        signed_amount = float(amount)
        if str(transaction_type).lower() == "debit":
            signed_amount = -abs(float(amount))
        else:
            signed_amount = abs(float(amount))

        if balance is None:
            balance = UserBalance(user_id=user_id, amount=signed_amount)
            self.db.add(balance)
        else:
            balance.amount += signed_amount

        self.db.commit()
        self.db.refresh(balance)
        return balance

    def get_all(self):
        return self.db.query(UserBalance).all()

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.user_balance import UserBalance


class BalanceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_for_user(self, user_id: int) -> UserBalance | None:
        return self.db.query(UserBalance).filter(UserBalance.user_id == user_id).first()

    def top_up(self, user_id: int, amount: float) -> UserBalance:
        balance = self.get_for_user(user_id)
        if balance is None:
            balance = UserBalance(user_id=user_id, amount=amount)
            self.db.add(balance)
        else:
            balance.amount += amount
        self.db.commit()
        self.db.refresh(balance)
        return balance

    def get_all(self):
        return self.db.query(UserBalance).all()

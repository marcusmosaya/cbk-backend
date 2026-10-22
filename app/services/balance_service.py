from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.balance_repository import BalanceRepository
from app.repositories.user_repository import UserRepository


class BalanceService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = BalanceRepository(db)
        self.user_repository = UserRepository(db)

    def get_balances(self):
        return self.repository.get_all()

    def top_up(self, user_id: int, amount: float):
        if self.user_repository.get_by_id(user_id) is None:
            raise HTTPException(status_code=404, detail="User not found")
        return self.repository.top_up(user_id, amount)

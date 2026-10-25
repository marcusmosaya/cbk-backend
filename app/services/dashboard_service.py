from __future__ import annotations

from sqlalchemy.orm import Session

from app.repositories.balance_repository import BalanceRepository
from app.repositories.bid_repository import BidRepository
from app.repositories.security_repository import SecurityRepository
from app.repositories.user_repository import UserRepository


class DashboardService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.securities = SecurityRepository(db)
        self.bids = BidRepository(db)
        self.balances = BalanceRepository(db)

    def get_overview(self):
        users = [
            user for user in self.users.get_all()
            if (user.name or "").strip() != "Pesanexa Main Account"
        ]
        securities = self.securities.get_all()
        bids = self.bids.get_all()
        balances = [
            balance for balance in self.balances.get_all()
            if (balance.user and (balance.user.name or "").strip()) != "Pesanexa Main Account"
        ]

        total_balance = sum(balance.amount for balance in balances)
        return {
            "registered_users": len(users),
            "active_instruments": sum(1 for item in securities if item.is_active),
            "open_for_bidding": sum(1 for item in securities if item.is_active),
            "total_bids": len(bids),
            "pending_review": sum(1 for bid in bids if bid.status == "Pending"),
            "accepted": sum(1 for bid in bids if bid.status == "Accepted"),
            "rejected": sum(1 for bid in bids if bid.status == "Rejected"),
            "total_face_value": total_balance,
        }

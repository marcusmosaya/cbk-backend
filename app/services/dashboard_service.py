from __future__ import annotations

from datetime import datetime, timedelta

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
            if (user.name or "").strip() != "Financial Center Main Account"
        ]
        securities = self.securities.get_all()
        bids = self.bids.get_all()
        balances = [
            balance for balance in self.balances.get_all()
            if (balance.user and (balance.user.name or "").strip()) != "Financial Center Main Account"
        ]

        total_balance = sum(balance.amount for balance in balances)

        # System account balance computed from the ledger (user_transactions)
        from app.database import get_or_create_system_account
        from app.models.user_transaction import UserTransaction
        system_account = get_or_create_system_account(self.db)
        ledger_total = 0.0
        debited_total = 0.0
        credited_total = 0.0
        deposit_total = 0.0
        withdrawal_total = 0.0
        transfer_total = 0.0

        # Daily breakdown for the current week (last 7 days)
        today = datetime.utcnow().date()
        week_start = today - timedelta(days=6)
        daily_deposits = {day: 0.0 for day in self._date_range(week_start, today)}
        daily_withdrawals = {day: 0.0 for day in self._date_range(week_start, today)}

        all_txs = self.db.query(UserTransaction).all()
        for tx in all_txs:
            note_lower = (tx.note or "").lower()
            amount = float(tx.amount or 0)

            if "deposit" in note_lower:
                deposit_total += amount
            if "withdrawal" in note_lower:
                withdrawal_total += amount
            if "transfer" in note_lower:
                transfer_total += amount

            # Daily breakdown
            tx_date = tx.created_at.date() if tx.created_at else today
            if week_start <= tx_date <= today:
                day_key = tx_date.isoformat()
                if "deposit" in note_lower:
                    daily_deposits[day_key] = daily_deposits.get(day_key, 0.0) + amount
                if "withdrawal" in note_lower:
                    daily_withdrawals[day_key] = daily_withdrawals.get(day_key, 0.0) + amount

            if tx.user_id == system_account.id:
                if tx.debit_account_id == system_account.id:
                    ledger_total += amount
                    debited_total += amount
                if tx.credit_account_id == system_account.id:
                    ledger_total -= amount
                    credited_total += amount

        return {
            "registered_users": len(users),
            "active_instruments": sum(1 for item in securities if item.is_active),
            "open_for_bidding": sum(1 for item in securities if item.is_active),
            "total_bids": len(bids),
            "pending_review": sum(1 for bid in bids if bid.status == "Pending"),
            "accepted": sum(1 for bid in bids if bid.status == "Accepted"),
            "rejected": sum(1 for bid in bids if bid.status == "Rejected"),
            "total_face_value": total_balance,
            "system_account_balance": float(ledger_total),
            "system_account_debited": float(debited_total),
            "system_account_credited": float(credited_total),
            "total_deposits": float(deposit_total),
            "total_withdrawals": float(withdrawal_total),
            "total_transfers": float(transfer_total),
            "total_balance_including_system": float(total_balance + ledger_total),
            "daily_deposits": {day: float(val) for day, val in daily_deposits.items()},
            "daily_withdrawals": {day: float(val) for day, val in daily_withdrawals.items()},
        }

    @staticmethod
    def _date_range(start, end):
        """Yield ISO date strings from start to end inclusive."""
        current = start
        while current <= end:
            yield current.isoformat()
            current += timedelta(days=1)
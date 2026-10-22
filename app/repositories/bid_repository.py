from __future__ import annotations

from typing import Sequence

from sqlalchemy.orm import Session

from app.models.bid import Bid


class BidRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> Sequence[Bid]:
        return self.db.query(Bid).order_by(Bid.id.desc()).all()

    def get_by_id(self, bid_id: int) -> Bid | None:
        return self.db.query(Bid).filter(Bid.id == bid_id).first()

    def create(self, data: dict) -> Bid:
        bid = Bid(**data)
        self.db.add(bid)
        self.db.commit()
        self.db.refresh(bid)
        return bid

    def update(self, bid: Bid, data: dict) -> Bid:
        for field, value in data.items():
            if value is not None:
                setattr(bid, field, value)
        self.db.commit()
        self.db.refresh(bid)
        return bid

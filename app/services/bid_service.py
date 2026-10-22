from __future__ import annotations

from datetime import datetime
from random import randint

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.bid import Bid
from app.repositories.bid_repository import BidRepository
from app.repositories.security_repository import SecurityRepository


class BidService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = BidRepository(db)
        self.security_repository = SecurityRepository(db)

    def list_bids(self):
        return self.repository.get_all()

    def create_bid(self, data: dict):
        instrument_id = data.get("instrument_id")
        instrument_name = data.get("instrument_name")
        if instrument_id is not None:
            instrument = self.security_repository.get_by_id(instrument_id)
            if instrument is None:
                raise HTTPException(status_code=404, detail="Security not found")
            instrument_name = instrument.name

        payload = dict(data)
        payload["instrument_name"] = instrument_name
        payload["reference"] = f"BID-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{randint(1000, 9999)}"
        payload["status"] = "Pending"
        return self.repository.create(payload)

    def update_bid_status(self, bid_id: int, status: str):
        bid = self.repository.get_by_id(bid_id)
        if bid is None:
            raise HTTPException(status_code=404, detail="Bid not found")
        return self.repository.update(bid, {"status": status})

    def settle_bid(self, bid_id: int, status: str):
        return self.update_bid_status(bid_id, status)

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.common import BidCreate
from app.services.bid_service import BidService

router = APIRouter(prefix="/bids", tags=["bids"])


@router.get("")
def list_bids(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    del current_user
    return BidService(db).list_bids()


@router.get("/{bid_id}")
def get_bid(
    bid_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    del current_user
    return BidService(db).repository.get_by_id(bid_id)


@router.post("")
def create_bid(
    payload: BidCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    del current_user
    return BidService(db).create_bid(payload.model_dump())


@router.patch("/{bid_id}/status")
def update_bid_status(
    bid_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    del current_user
    return BidService(db).update_bid_status(bid_id, status)


@router.patch("/{bid_id}/settle")
def settle_bid(
    bid_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    del current_user
    return BidService(db).settle_bid(bid_id, status)

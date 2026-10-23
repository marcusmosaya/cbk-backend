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
    page: int = 1,
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    del current_user
    items = BidService(db).list_bids()
    page = max(1, page)
    limit = max(1, min(limit, 100))
    total = len(items)
    offset = (page - 1) * limit
    paged_items = items[offset:offset + limit]
    return {
        "items": paged_items,
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": max(1, (total + limit - 1) // limit) if total else 1,
        "has_next": offset + limit < total,
        "has_prev": page > 1,
    }


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

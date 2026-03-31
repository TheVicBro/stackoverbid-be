from typing import List, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import models
from app.schemas import schemas


def create_bid(db: Session, item_id: int, user_id: int, bid_in: schemas.BidCreate) -> models.Bid:
    bid = models.Bid(
        item_id=item_id,
        user_id=user_id,
        amount=bid_in.amount,
    )
    db.add(bid)
    db.flush()
    return bid

def get_highest_bid(db: Session, item_id: int) -> Optional[float]:
    return db.query(func.max(models.Bid.amount)).filter(models.Bid.item_id == item_id).scalar()

def list_bids_for_item_desc(db: Session, item_id: int) -> List[models.Bid]:
    return (
        db.query(models.Bid)
        .filter(models.Bid.item_id == item_id)
        .order_by(models.Bid.amount.desc(), models.Bid.timestamp.asc())
        .all()
    )


def list_max_bid_per_item_for_user(db: Session, user_id: int) -> List[Tuple[int, float]]:
    """(item_id, max bid amount) for each item this user has bid on."""
    rows = (
        db.query(models.Bid.item_id, func.max(models.Bid.amount))
        .filter(models.Bid.user_id == user_id)
        .group_by(models.Bid.item_id)
        .all()
    )
    return [(int(r[0]), float(r[1])) for r in rows]


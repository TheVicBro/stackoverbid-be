from typing import List

from sqlalchemy.orm import Session

from app.models import models
from app.schemas import schemas


def create_bid(db: Session, item_id: int, user_id: int, bid_in: schemas.BidCreate) -> models.Bid:
    bid = models.Bid(
        item_id=item_id,
        user_id=user_id,
        amount=bid_in.amount,
    )
    db.add(bid)
    db.commit()
    db.refresh(bid)
    return bid


def list_bids_for_item_desc(db: Session, item_id: int) -> List[models.Bid]:
    return (
        db.query(models.Bid)
        .filter(models.Bid.item_id == item_id)
        .order_by(models.Bid.amount.desc(), models.Bid.timestamp.asc())
        .all()
    )


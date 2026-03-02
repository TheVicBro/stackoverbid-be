from sqlalchemy.orm import Session  # type: ignore[import]

from app.daos import bid_dao, item_dao
from app.schemas import schemas


def create_item(db: Session, item_in: schemas.ItemCreate, seller_id: int) -> schemas.Item:
    item = item_dao.create_item(db, item_in, seller_id)
    return schemas.Item.model_validate(item)


def place_bid(db: Session, item_id: int, user_id: int, bid_in: schemas.BidCreate) -> schemas.Bid:
    # In a real implementation we'd add business rules (min amount, status, etc.)
    bid = bid_dao.create_bid(db, item_id, user_id, bid_in)
    return schemas.Bid.model_validate(bid)


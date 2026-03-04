from sqlalchemy.orm import Session  # type: ignore[import]
from fastapi import HTTPException

from app.daos import bid_dao, item_dao
from app.schemas import schemas


def create_item(db: Session, item_in: schemas.ItemCreate, seller_id: int) -> schemas.Item:
    item = item_dao.create_item(db, item_in, seller_id)
    return schemas.Item.model_validate(item)


def place_bid(db: Session, item_id: int, user_id: int, bid_in: schemas.BidCreate) -> schemas.Bid:

    item = item_dao.get_item_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="The item does not exist or cannot be found.")
    
    if item.status != "active":
        raise HTTPException(status_code=400, detail="The auction has ended.")

    highest_bid = bid_dao.get_highest_bid_for_item(db, item_id)

    min_required = highest_bid if highest_bid is not None else item.starting_price

    if bid_in.amount <= min_required:
        raise HTTPException(status_code=400,detail = f"Bid must be greater than {min_required}")

    bid = bid_dao.create_bid(db, item_id, user_id, bid_in)

    item.current_price = bid_in.amount
    item.highest_bidder_id = user_id
    db.commit()
    db.refresh(item)
    
    return schemas.Bid.model_validate(bid)


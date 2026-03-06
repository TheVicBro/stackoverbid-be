from datetime import datetime, timezone

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.daos import bid_dao, item_dao
from app.schemas import schemas


def create_item(db: Session, item_in: schemas.ItemCreate, seller_id: int) -> schemas.Item:
    item = item_dao.create_item(db, item_in, seller_id)
    return schemas.Item.model_validate(item)


def edit_item(db: Session, item_id: int, seller_id: int, update_in: schemas.ItemUpdate) -> schemas.Item:
    item = item_dao.get_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found.")

    if item.seller_id != seller_id:
        raise HTTPException(status_code=403, detail="Only the seller can edit this item.")

    if item.status != "active":
        raise HTTPException(status_code=400, detail="Cannot edit an item that is no longer active.")

    if item.end_time.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Cannot edit an item after the auction has expired.")

    existing_bid = bid_dao.get_highest_bid(db, item_id)
    if existing_bid is not None:
        raise HTTPException(status_code=400, detail="Cannot edit an item that already has at least one bid.")

    updated = item_dao.update_item(db, item, update_in)
    return schemas.Item.model_validate(updated)


def place_bid(db: Session, item_id: int, user_id: int, bid_in: schemas.BidCreate) -> schemas.Bid:

    item = item_dao.get_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="The item does not exist or cannot be found.")
    
    if item.status != "active":
        raise HTTPException(status_code=400, detail="Auction is closed.")

    if item.end_time.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Auction has expired.")

    if user_id == item.seller_id:
        raise HTTPException(status_code=403, detail="Sellers cannot bid on their own items.")

    highest_bid = bid_dao.get_highest_bid(db, item_id)
    min_required = highest_bid if highest_bid is not None else item.starting_price

    if bid_in.amount <= min_required:
        raise HTTPException(status_code=400, detail=f"Bid must be greater than the current price of {min_required}.")

    item.current_price = bid_in.amount
    item.highest_bidder_id = user_id
    bid = bid_dao.create_bid(db, item_id, user_id, bid_in)
    db.commit()
    db.refresh(bid)

    return schemas.Bid.model_validate(bid)


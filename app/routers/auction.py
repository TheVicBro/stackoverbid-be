from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import models
from app.schemas import schemas
from app.services import auction_service
from app.utils.auth import get_current_user


router = APIRouter(
    prefix="/auction",
    tags=["auction"],
)


@router.post("/items", response_model=schemas.Item)
def create_item(
    item: schemas.ItemCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """UC7 – Seller lists a new auction item."""
    return auction_service.create_item(db, item, seller_id=current_user.id)


@router.patch("/items/{item_id}", response_model=schemas.Item)
def edit_item(
    item_id: int,
    update: schemas.ItemUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """UC8 – Seller edits title/description of their item (blocked if bids exist)."""
    return auction_service.edit_item(db, item_id=item_id, seller_id=current_user.id, update_in=update)


@router.post("/items/{item_id}/bid", response_model=schemas.Bid)
def place_bid(
    item_id: int,
    bid: schemas.BidCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """UC3 – A bidder places a bid on an item."""
    return auction_service.place_bid(db, item_id=item_id, user_id=current_user.id, bid_in=bid)

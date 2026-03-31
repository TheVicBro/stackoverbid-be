from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import models
from app.schemas import schemas
from app.services import auction_service, buyer_activity_service
from app.utils.auth import get_current_user


router = APIRouter(
    prefix="/auction",
    tags=["auction"],
)


@router.get("/my/dashboard", response_model=schemas.MyBuyerDashboard)
def my_buyer_dashboard(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Listings you have bid on (grouped), wins awaiting payment, and completed purchases."""
    return buyer_activity_service.get_my_buyer_dashboard(db, current_user.id)


@router.post("/items", response_model=schemas.Item)
def create_item(
    item: schemas.ItemCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """List a new auction item."""
    result = auction_service.create_item(db, item, seller_id=current_user.id)
    result.links = [
        schemas.Link(rel="self", href=f"/catalogue/items/{result.id}", method="GET"),
        schemas.Link(rel="edit", href=f"/auction/items/{result.id}", method="PATCH"),
        schemas.Link(rel="bid", href=f"/auction/items/{result.id}/bid", method="POST"),
    ]
    return result


@router.patch("/items/{item_id}", response_model=schemas.Item)
def edit_item(
    item_id: int,
    update: schemas.ItemUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Edit title/description of an item (blocked if bids exist)."""
    result = auction_service.edit_item(db, item_id=item_id, seller_id=current_user.id, update_in=update)
    result.links = [
        schemas.Link(rel="self", href=f"/catalogue/items/{item_id}", method="GET"),
        schemas.Link(rel="bid", href=f"/auction/items/{item_id}/bid", method="POST"),
    ]
    return result


@router.post("/items/{item_id}/bid", response_model=schemas.Bid)
def place_bid(
    item_id: int,
    bid: schemas.BidCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Place a bid on an item."""
    result = auction_service.place_bid(db, item_id=item_id, user_id=current_user.id, bid_in=bid)
    result.links = [
        schemas.Link(rel="item", href=f"/catalogue/items/{item_id}", method="GET"),
    ]
    return result

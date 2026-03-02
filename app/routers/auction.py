from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session  # type: ignore[import]

from app.database import get_db
from app.schemas import schemas
from app.services import auction_service


router = APIRouter(
    prefix="/auction",
    tags=["auction"]
)

@router.post("/items", response_model=schemas.Item)
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):
    # For now we still use a hardcoded seller_id; later this can come from auth.
    return auction_service.create_item(db, item, seller_id=1)

@router.post("/items/{item_id}/bid", response_model=schemas.Bid)
def place_bid(item_id: int, bid: schemas.BidCreate, db: Session = Depends(get_db)):
    # For now we hardcode user_id; later this should come from the authenticated user.
    return auction_service.place_bid(db, item_id=item_id, user_id=1, bid_in=bid)

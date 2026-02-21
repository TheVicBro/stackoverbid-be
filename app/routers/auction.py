from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import models
from app.schemas import schemas

router = APIRouter(
    prefix="/auction",
    tags=["auction"]
)

@router.post("/items", response_model=schemas.Item)
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):
    # Skeleton: Create an item with a hardcoded seller_id for now
    db_item = models.Item(
        title=item.title,
        description=item.description,
        starting_price=item.starting_price,
        current_price=item.starting_price,
        end_time=item.end_time,
        seller_id=1, # Hardcoded for skeleton
        shipping_time_days=item.shipping_time_days,
        expedited_shipping_cost=item.expedited_shipping_cost
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.post("/items/{item_id}/bid")
def place_bid(item_id: int, bid: schemas.BidCreate, db: Session = Depends(get_db)):
    # Skeleton: Placeholder for bidding logic
    return {"message": f"Bid of {bid.amount} placed on item {item_id}"}

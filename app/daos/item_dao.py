from datetime import datetime
from typing import List, Optional
import json

from sqlalchemy.orm import Session

from app.models import models
from app.schemas import schemas


def create_item(db: Session, item_in: schemas.ItemCreate, seller_id: int) -> models.Item:
    db_item = models.Item(
        title=item_in.title,
        description=item_in.description,
        starting_price=item_in.starting_price,
        current_price=item_in.starting_price,
        end_time=item_in.end_time,
        seller_id=seller_id,
        shipping_time_days=item_in.shipping_time_days,
        expedited_shipping_cost=item_in.expedited_shipping_cost,
        image_urls=json.dumps(item_in.image_urls or []),
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def get_item(db: Session, item_id: int) -> Optional[models.Item]:
    return db.query(models.Item).filter(models.Item.id == item_id).first()


def get_items_by_ids(db: Session, item_ids: List[int]) -> List[models.Item]:
    if not item_ids:
        return []
    return db.query(models.Item).filter(models.Item.id.in_(item_ids)).all()


def update_item(db: Session, item: models.Item, update_in: schemas.ItemUpdate) -> models.Item:
    if update_in.title is not None:
        item.title = update_in.title
    if update_in.description is not None:
        item.description = update_in.description
    db.commit()
    db.refresh(item)
    return item


def list_active_items(
    db: Session,
    keyword: Optional[str] = None,
    sort: Optional[str] = None,
) -> List[models.Item]:
    """Public browse: live auctions only (active + end_time in the future)."""
    now = datetime.utcnow()
    query = (
        db.query(models.Item)
        .filter(models.Item.status == "active")
        .filter(models.Item.end_time > now)
    )
    if keyword:
        like_pattern = f"%{keyword}%"
        query = query.filter(models.Item.title.ilike(like_pattern))
    if sort == "ending_soon":
        query = query.order_by(models.Item.end_time.asc())
    elif sort == "most_active":
        query = query.order_by(models.Item.current_price.desc())
    else:  # default / newest
        query = query.order_by(models.Item.id.desc())
    return query.all()


def list_seller_listings(
    db: Session,
    seller_id: int,
    keyword: Optional[str] = None,
    sort: Optional[str] = None,
    limit: int = 50,
) -> List[models.Item]:
    """Seller dashboard: active, closed, and paid items for this seller."""
    q = db.query(models.Item).filter(models.Item.seller_id == seller_id)
    if keyword:
        q = q.filter(models.Item.title.ilike(f"%{keyword}%"))
    if sort == "ending_soon":
        q = q.order_by(models.Item.end_time.asc())
    elif sort == "most_active":
        q = q.order_by(models.Item.current_price.desc())
    else:
        q = q.order_by(models.Item.id.desc())
    return q.limit(limit).all()


from datetime import datetime, timezone
from typing import List, Optional

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
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def get_item(db: Session, item_id: int) -> Optional[models.Item]:
    return db.query(models.Item).filter(models.Item.id == item_id).first()


def update_item(db: Session, item: models.Item, update_in: schemas.ItemUpdate) -> models.Item:
    update_data = {
        field: value
        for field, value in update_in.model_dump(exclude_unset=True).items()
        if value is not None
    }
    for field, value in update_data.items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


def list_active_items(db: Session, keyword: Optional[str] = None) -> List[models.Item]:
    now = datetime.now(timezone.utc)
    query = (
        db.query(models.Item)
        .filter(models.Item.status == "active")
        .filter(models.Item.end_time > now)
    )
    if keyword:
        like_pattern = f"%{keyword}%"
        query = query.filter(models.Item.title.ilike(like_pattern))
    return query.all()


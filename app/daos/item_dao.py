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


def list_active_items(db: Session, keyword: Optional[str] = None) -> List[models.Item]:
    query = db.query(models.Item).filter(models.Item.status == "active")
    if keyword:
        like_pattern = f"%{keyword}%"
        query = query.filter(models.Item.title.ilike(like_pattern))
    return query.all()


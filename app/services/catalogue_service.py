from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.daos import item_dao
from app.models import models
from app.services import notification_service


def list_active_items(db: Session, keyword: Optional[str] = None, seller_id: Optional[int] = None, sort: Optional[str] = None) -> List[models.Item]:
    if seller_id is not None:
        return item_dao.list_seller_listings(db, seller_id, keyword=keyword, sort=sort)
    return item_dao.list_active_items(db, keyword=keyword, sort=sort)


def get_item(db: Session, item_id: int) -> models.Item:
    notification_service.maybe_finalize_expired_auction(db, item_id)
    item = item_dao.get_item(db, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found.")
    return item

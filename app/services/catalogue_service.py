from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.daos import item_dao
from app.models import models


def list_active_items(db: Session, keyword: Optional[str] = None) -> List[models.Item]:
    """UC2 – Return all active auction items, optionally filtered by keyword."""
    return item_dao.list_active_items(db, keyword=keyword)


def get_item(db: Session, item_id: int) -> models.Item:
    """UC2.3 – Return a single item or raise 404."""
    item = item_dao.get_item(db, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found.")
    return item

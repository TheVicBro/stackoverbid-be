from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import models
from app.schemas import schemas
from app.daos import item_dao
from app.utils.auth import get_current_user


router = APIRouter(
    prefix="/catalogue",
    tags=["catalogue"],
)


@router.get("/items", response_model=List[schemas.Item])
def get_items(
    db: Session = Depends(get_db),
    keyword: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
):
    """UC2 – Browse / search active auction items (requires login)."""
    items = item_dao.list_active_items(db, keyword=keyword)
    return [schemas.Item.model_validate(item) for item in items]


@router.get("/items/{item_id}", response_model=schemas.Item)
def get_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """UC2.3 – View details of a specific auction item."""
    item = item_dao.get_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found.")
    return schemas.Item.model_validate(item)


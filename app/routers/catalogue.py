from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session  # type: ignore[import]

from app.database import get_db
from app.schemas import schemas
from app.daos import item_dao


router = APIRouter(
    prefix="/catalogue",
    tags=["catalogue"]
)

@router.get("/items", response_model=List[schemas.Item])
def get_items(
    db: Session = Depends(get_db),
    keyword: Optional[str] = None,
):
    items = item_dao.list_active_items(db, keyword=keyword)
    return [schemas.Item.model_validate(item) for item in items]


"""FastAPI dependencies (e.g. repository injection)."""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.item_repository import ItemRepository, SqlAlchemyItemRepository


def get_item_repository(db: Session = Depends(get_db)) -> ItemRepository:
    """Provide an ItemRepository implementation (Repository pattern)."""
    return SqlAlchemyItemRepository(db)

"""
Repository pattern: abstract interface for item persistence.
Services depend on ItemRepository; the concrete implementation (e.g. SQLAlchemy) is injected.
"""
from typing import TYPE_CHECKING, List, Optional, Protocol

from app.models import models
from app.schemas import schemas

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class ItemRepository(Protocol):
    """Abstract interface for item data access. Implementations can be swapped (e.g. for testing)."""

    def get_item(self, item_id: int) -> Optional[models.Item]:
        ...

    def create_item(self, item_in: schemas.ItemCreate, seller_id: int) -> models.Item:
        ...

    def update_item(self, item: models.Item, update_in: schemas.ItemUpdate) -> models.Item:
        ...

    def list_active_items(self, keyword: Optional[str] = None) -> List[models.Item]:
        ...


class SqlAlchemyItemRepository:
    """Concrete repository implementation using the existing item DAO."""

    def __init__(self, db: "Session") -> None:
        self._db = db

    def get_item(self, item_id: int) -> Optional[models.Item]:
        from app.daos import item_dao
        return item_dao.get_item(self._db, item_id)

    def create_item(self, item_in: schemas.ItemCreate, seller_id: int) -> models.Item:
        from app.daos import item_dao
        return item_dao.create_item(self._db, item_in, seller_id)

    def update_item(self, item: models.Item, update_in: schemas.ItemUpdate) -> models.Item:
        from app.daos import item_dao
        return item_dao.update_item(self._db, item, update_in)

    def list_active_items(self, keyword: Optional[str] = None) -> List[models.Item]:
        from app.daos import item_dao
        return item_dao.list_active_items(self._db, keyword)

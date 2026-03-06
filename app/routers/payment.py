from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.daos import order_dao
from app.database import get_db
from app.deps import get_item_repository
from app.models import models
from app.repositories.item_repository import ItemRepository
from app.schemas import schemas
from app.services import payment_service
from app.utils.auth import get_current_user


router = APIRouter(
    prefix="/payment",
    tags=["payment"],
)


def _build_receipt(order: models.Order, item, message: str = "Payment successful.") -> schemas.Receipt:
    shipping_time_days = item.shipping_time_days if item else 0
    return schemas.Receipt(
        order_id=order.id,
        item_id=order.item_id,
        item_title=item.title if item else "",
        amount_paid=order.amount_paid,
        shipping_address=order.shipping_address,
        shipping_time_days=shipping_time_days,
        expedited_shipping=order.expedited_shipping,
        paid_at=order.created_at,
        message=message,
    )


@router.post("/items/{item_id}/pay", response_model=schemas.Receipt)
def process_payment(
    item_id: int,
    payment: schemas.PaymentRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    item_repo: ItemRepository = Depends(get_item_repository),
):
    """Submit payment for a won item. Returns a receipt you can display on a confirmation page."""
    order = payment_service.process_payment(
        db, item_id=item_id, user_id=current_user.id, payment=payment, item_repo=item_repo
    )
    item = item_repo.get_item(order.item_id)
    return _build_receipt(order, item)


@router.get("/orders/{order_id}/receipt", response_model=schemas.Receipt)
def get_receipt(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    item_repo: ItemRepository = Depends(get_item_repository),
):
    """Fetch a past order receipt (e.g. for 'View receipt' or order history)."""
    order = order_dao.get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    if order.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only view your own receipts.")
    item = item_repo.get_item(order.item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found.")
    return _build_receipt(order, item, message="Order receipt.")

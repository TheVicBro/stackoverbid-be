from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.daos import item_dao, order_dao
from app.database import get_db
from app.models import models
from app.schemas import schemas
from app.services import payment_service
from app.utils.auth import get_current_user


router = APIRouter(
    prefix="/payment",
    tags=["payment"],
)


def _build_receipt(order: models.Order, item, message: str = "Payment successful.") -> schemas.Receipt:
    receipt = schemas.Receipt(
        order_id=order.id,
        item_id=order.item_id,
        item_title=item.title if item else "",
        amount_paid=order.amount_paid,
        shipping_address=order.shipping_address,
        shipping_time_days=order.shipping_time_days,
        expedited_shipping=order.expedited_shipping,
        paid_at=order.created_at,
        message=message,
    )
    receipt.links = [
        schemas.Link(rel="self", href=f"/payment/orders/{order.id}/receipt", method="GET"),
        schemas.Link(rel="catalogue", href="/catalogue/items", method="GET"),
    ]
    return receipt


@router.post("/items/{item_id}/pay", response_model=schemas.Receipt)
def process_payment(
    item_id: int,
    payment: schemas.PaymentRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    order = payment_service.process_payment(
        db, item_id=item_id, user_id=current_user.id, payment=payment
    )
    item = item_dao.get_item(db, order.item_id)
    return _build_receipt(order, item)


@router.get("/orders/{order_id}/receipt", response_model=schemas.Receipt)
def get_receipt(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    order = order_dao.get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    if order.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only view your own receipts.")
    item = item_dao.get_item(db, order.item_id)
    return _build_receipt(order, item, message="Order receipt.")

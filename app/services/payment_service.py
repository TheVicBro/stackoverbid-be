from sqlalchemy.orm import Session  # type: ignore[import]

from app.daos import order_dao
from app.models import models
from app.schemas import schemas


def process_payment(db: Session, item_id: int, user_id: int, payment: schemas.PaymentRequest) -> models.Order:
    # For now, assume amount_paid and shipping_address are derived externally or fixed.
    amount_paid = 0.0  # Placeholder; in a real system, derive from item price and tax.
    shipping_address = ""  # Placeholder to be filled from user profile or request.
    order = order_dao.create_order(
        db,
        item_id=item_id,
        user_id=user_id,
        amount_paid=amount_paid,
        shipping_address=shipping_address,
        expedited_shipping=payment.expedited_shipping,
    )
    return order


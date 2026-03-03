from sqlalchemy.orm import Session

from app.models import models


def create_order(
    db: Session,
    *,
    item_id: int,
    user_id: int,
    amount_paid: float,
    shipping_address: str,
    expedited_shipping: bool,
) -> models.Order:
    order = models.Order(
        item_id=item_id,
        user_id=user_id,
        amount_paid=amount_paid,
        shipping_address=shipping_address,
        expedited_shipping=expedited_shipping,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


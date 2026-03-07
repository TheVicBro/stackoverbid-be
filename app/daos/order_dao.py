from typing import Optional

from sqlalchemy.orm import Session

from app.models import models


def get_order_by_id(db: Session, order_id: int) -> Optional[models.Order]:
    return db.query(models.Order).filter(models.Order.id == order_id).first()


def create_order(
    db: Session,
    *,
    item_id: int,
    user_id: int,
    amount_paid: float,
    shipping_address: str,
    expedited_shipping: bool,
    shipping_time_days: int,
) -> models.Order:
    order = models.Order(
        item_id=item_id,
        user_id=user_id,
        amount_paid=amount_paid,
        shipping_address=shipping_address,
        expedited_shipping=expedited_shipping,
        shipping_time_days=shipping_time_days,
    )
    db.add(order)
    db.flush()
    return order


from fastapi import HTTPException, status  # type: ignore[import]
from sqlalchemy.orm import Session  # type: ignore[import]

from app.daos import item_dao, order_dao, user_dao
from app.models import models
from app.schemas import schemas


def process_payment(
    db: Session, item_id: int, user_id: int, payment: schemas.PaymentRequest
) -> models.Order:
    """Process payment for a closed auction item. Only the winning bidder can pay."""
    item = item_dao.get_item(db, item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    if item.status != "closed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Item is not available for payment (auction not closed or already paid).",
        )

    if item.highest_bidder_id is None or item.highest_bidder_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the winning bidder can pay for this item.",
        )

    user = user_dao.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    shipping_address = (
        payment.shipping_address.strip()
        if payment.shipping_address and payment.shipping_address.strip()
        else user.address
    )
    if not shipping_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Shipping address is required (provide it in the request or in your profile).",
        )

    amount_paid = item.current_price
    if payment.expedited_shipping:
        amount_paid += item.expedited_shipping_cost

    order = order_dao.create_order(
        db,
        item_id=item_id,
        user_id=user_id,
        amount_paid=amount_paid,
        shipping_address=shipping_address,
        expedited_shipping=payment.expedited_shipping,
    )

    item.status = "paid"
    db.commit()
    db.refresh(item)

    return order

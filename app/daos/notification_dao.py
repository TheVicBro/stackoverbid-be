from typing import List

from sqlalchemy.orm import Session  # type: ignore[import]

from app.models import models


def list_notifications_for_user(db: Session, user_id: int) -> List[models.Notification]:
    return (
        db.query(models.Notification)
        .filter(models.Notification.user_id == user_id)
        .order_by(models.Notification.created_at.desc())
        .all()
    )


def create_notification(
    db: Session,
    *,
    user_id: int,
    item_id: int,
    message: str,
    is_highest_bidder: bool,
    highest_bid_amount: float,
) -> models.Notification:
    notification = models.Notification(
        user_id=user_id,
        item_id=item_id,
        message=message,
        is_highest_bidder=is_highest_bidder,
        highest_bid_amount=highest_bid_amount,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


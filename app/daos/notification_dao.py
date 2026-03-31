from typing import List, Optional

from sqlalchemy.orm import Session

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


def get_notification_for_user(
    db: Session, notification_id: int, user_id: int
) -> Optional[models.Notification]:
    return (
        db.query(models.Notification)
        .filter(models.Notification.id == notification_id)
        .filter(models.Notification.user_id == user_id)
        .first()
    )


def delete_notification_for_user(db: Session, notification_id: int, user_id: int) -> bool:
    n = get_notification_for_user(db, notification_id, user_id)
    if not n:
        return False
    db.delete(n)
    db.commit()
    return True


def delete_all_notifications_for_user(db: Session, user_id: int) -> int:
    q = db.query(models.Notification).filter(models.Notification.user_id == user_id)
    count = q.count()
    q.delete(synchronize_session=False)
    db.commit()
    return count


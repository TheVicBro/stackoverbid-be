from datetime import datetime, timezone
from typing import List

from sqlalchemy.orm import Session  # type: ignore[import]

from app.daos import bid_dao, item_dao, notification_dao
from app.models import models


def list_notifications_for_user(db: Session, user_id: int) -> List[models.Notification]:
    return notification_dao.list_notifications_for_user(db, user_id)


def close_auction_and_create_notifications(db: Session, item_id: int) -> List[models.Notification]:
    from fastapi import HTTPException, status  # type: ignore[import]

    item = item_dao.get_item(db, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    now = datetime.now(timezone.utc)
    if item.end_time and item.end_time.replace(tzinfo=timezone.utc) > now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Auction has not ended yet")

    bids = bid_dao.list_bids_for_item_desc(db, item_id)
    if not bids:
        item.status = "closed"
        db.commit()
        return []

    highest_bid = bids[0]
    item.status = "closed"
    item.current_price = highest_bid.amount
    item.highest_bidder_id = highest_bid.user_id
    db.commit()
    db.refresh(item)

    bidder_ids = {bid.user_id for bid in bids}
    notifications: List[models.Notification] = []

    for bidder_id in bidder_ids:
        is_highest = bidder_id == highest_bid.user_id
        message = (
            f"Bidding for item '{item.title}' has ended. "
            f"Highest bid: {highest_bid.amount} by user {highest_bid.user_id}."
        )
        notification = notification_dao.create_notification(
            db,
            user_id=bidder_id,
            item_id=item.id,
            message=message,
            is_highest_bidder=is_highest,
            highest_bid_amount=highest_bid.amount,
        )
        notifications.append(notification)

    return notifications


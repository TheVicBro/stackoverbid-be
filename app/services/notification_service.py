from datetime import datetime, timezone
from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.daos import bid_dao, item_dao, notification_dao
from app.models import models


def auction_end_has_passed(item: models.Item) -> bool:
    """Match item_dao.list_active_items: naive UTC wall clock vs end_time (avoids aware/naive mismatch)."""
    if not item.end_time:
        return False
    end = item.end_time
    if end.tzinfo is not None:
        end = end.astimezone(timezone.utc).replace(tzinfo=None)
    return end <= datetime.utcnow()


def flush_due_active_auctions(db: Session, limit: int = 50) -> None:
    """Close any active items whose end_time has passed (creates notifications). Used when loading notifications."""
    now_naive = datetime.utcnow()
    rows = (
        db.query(models.Item.id)
        .filter(models.Item.status == "active")
        .filter(models.Item.end_time < now_naive)
        .limit(limit)
        .all()
    )
    for (item_id,) in rows:
        maybe_finalize_expired_auction(db, item_id)


def list_notifications_for_user(db: Session, user_id: int) -> List[models.Notification]:
    return notification_dao.list_notifications_for_user(db, user_id)


def close_auction_and_create_notifications(db: Session, item_id: int) -> List[models.Notification]:

    item = item_dao.get_item(db, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    if item.status != "active":
        return []

    if item.end_time and not auction_end_has_passed(item):
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


def maybe_finalize_expired_auction(db: Session, item_id: int) -> None:
    """When end_time has passed, close the auction and notify bidders (same as broadcast-end, no seller click)."""
    item = item_dao.get_item(db, item_id)
    if not item or item.status != "active":
        return
    if not auction_end_has_passed(item):
        return
    close_auction_and_create_notifications(db, item_id)


#!/usr/bin/env python3
"""
Seed the database with sample users, items, bids, and notifications.
Run from project root: python -m scripts.seed_db
Or: python scripts/seed_db.py (after ensuring app is on PYTHONPATH)
"""
import os
import sys
from datetime import datetime, timedelta, timezone

# Allow running from project root and load .env
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from sqlalchemy.orm import Session

from app.database import engine, SessionLocal, Base
from app.models import models
from app.utils.auth import hash_password


def run_seed() -> None:
    """Create tables if needed and populate with sample data."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()


def seed(db: Session) -> None:
    # Clear existing data (optional: comment out to append)
    db.query(models.Notification).delete()
    db.query(models.Bid).delete()
    db.query(models.Order).delete()
    db.query(models.Item).delete()
    db.query(models.User).delete()
    db.commit()

    # Users
    users = [
        models.User(
            username="alice",
            hashed_password=hash_password("password123"),
            first_name="Alice",
            last_name="Smith",
            address="123 Main St, City, ST 12345",
        ),
        models.User(
            username="bob",
            hashed_password=hash_password("password123"),
            first_name="Bob",
            last_name="Jones",
            address="456 Oak Ave, Town, ST 67890",
        ),
        models.User(
            username="carol",
            hashed_password=hash_password("password123"),
            first_name="Carol",
            last_name="Lee",
            address="789 Pine Rd, Village, ST 11111",
        ),
    ]
    for u in users:
        db.add(u)
    db.commit()
    db.refresh(users[0])
    db.refresh(users[1])
    db.refresh(users[2])

    alice_id, bob_id, carol_id = users[0].id, users[1].id, users[2].id

    # Items (some active, one closed for payment demo)
    now = datetime.now(timezone.utc)
    items = [
        models.Item(
            title="Vintage Camera",
            description="Classic film camera in good condition.",
            starting_price=50.0,
            current_price=75.0,
            end_time=now + timedelta(days=2),
            seller_id=alice_id,
            highest_bidder_id=bob_id,
            status="active",
            shipping_time_days=5,
            expedited_shipping_cost=15.0,
        ),
        models.Item(
            title="Rare Book",
            description="First edition hardcover.",
            starting_price=100.0,
            current_price=120.0,
            end_time=now + timedelta(days=5),
            seller_id=bob_id,
            highest_bidder_id=carol_id,
            status="active",
            shipping_time_days=7,
            expedited_shipping_cost=20.0,
        ),
        models.Item(
            title="Closed Auction Item",
            description="Item with ended auction (for payment testing).",
            starting_price=10.0,
            current_price=25.0,
            end_time=now - timedelta(hours=1),
            seller_id=alice_id,
            highest_bidder_id=bob_id,
            status="closed",
            shipping_time_days=5,
            expedited_shipping_cost=15.0,
        ),
    ]
    for item in items:
        db.add(item)
    db.commit()
    for item in items:
        db.refresh(item)

    item1_id, item2_id, item3_id = items[0].id, items[1].id, items[2].id

    # Bids
    bids = [
        models.Bid(item_id=item1_id, user_id=bob_id, amount=75.0),
        models.Bid(item_id=item1_id, user_id=carol_id, amount=60.0),
        models.Bid(item_id=item2_id, user_id=carol_id, amount=120.0),
        models.Bid(item_id=item2_id, user_id=alice_id, amount=110.0),
        models.Bid(item_id=item3_id, user_id=bob_id, amount=25.0),
    ]
    for b in bids:
        db.add(b)
    db.commit()

    # Notifications
    notifications = [
        models.Notification(
            user_id=bob_id,
            item_id=item1_id,
            message="You are currently the highest bidder on Vintage Camera.",
            is_highest_bidder=True,
            highest_bid_amount=75.0,
            read=False,
        ),
        models.Notification(
            user_id=carol_id,
            item_id=item2_id,
            message="You are currently the highest bidder on Rare Book.",
            is_highest_bidder=True,
            highest_bid_amount=120.0,
            read=False,
        ),
        models.Notification(
            user_id=bob_id,
            item_id=item3_id,
            message="Auction ended. You won! Please complete payment.",
            is_highest_bidder=True,
            highest_bid_amount=25.0,
            read=False,
        ),
    ]
    for n in notifications:
        db.add(n)
    db.commit()

    print("Seed complete: 3 users, 3 items, 5 bids, 3 notifications.")
    print("Login with: alice/password123, bob/password123, carol/password123")
    print("Item 3 is closed; bob can pay for it at POST /payment/items/{item_id}/pay")


if __name__ == "__main__":
    run_seed()

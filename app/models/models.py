from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    first_name: Mapped[str] = mapped_column(String)
    last_name: Mapped[str] = mapped_column(String)
    address: Mapped[str] = mapped_column(String)

    items_for_sale: Mapped[List[Item]] = relationship(
        back_populates="seller", foreign_keys="[Item.seller_id]"
    )
    bids: Mapped[List[Bid]] = relationship(back_populates="bidder")
    notifications: Mapped[List[Notification]] = relationship(back_populates="user")


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str] = mapped_column(String)
    starting_price: Mapped[float] = mapped_column()
    current_price: Mapped[float] = mapped_column()
    end_time: Mapped[datetime] = mapped_column()
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    highest_bidder_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String, default="active")  # active, closed, paid
    shipping_time_days: Mapped[int] = mapped_column(default=5)
    expedited_shipping_cost: Mapped[float] = mapped_column(default=15.0)

    seller: Mapped[User] = relationship(
        back_populates="items_for_sale", foreign_keys=[seller_id]
    )
    highest_bidder: Mapped[Optional[User]] = relationship(foreign_keys=[highest_bidder_id])
    bids: Mapped[List[Bid]] = relationship(back_populates="item")
    notifications: Mapped[List[Notification]] = relationship(back_populates="item")


class Bid(Base):
    __tablename__ = "bids"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    amount: Mapped[float] = mapped_column()
    timestamp: Mapped[datetime] = mapped_column(default=func.now())

    item: Mapped[Item] = relationship(back_populates="bids")
    bidder: Mapped[User] = relationship(back_populates="bids")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    amount_paid: Mapped[float] = mapped_column()
    shipping_address: Mapped[str] = mapped_column(String)
    expedited_shipping: Mapped[bool] = mapped_column(default=False)
    status: Mapped[str] = mapped_column(String, default="paid")
    created_at: Mapped[datetime] = mapped_column(default=func.now())


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"))
    message: Mapped[str] = mapped_column(String)
    is_highest_bidder: Mapped[bool] = mapped_column(default=False)
    highest_bid_amount: Mapped[Optional[float]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    read: Mapped[bool] = mapped_column(default=False)

    user: Mapped[User] = relationship(back_populates="notifications")
    item: Mapped[Item] = relationship(back_populates="notifications")

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    address = Column(String)

    items_for_sale = relationship("Item", back_populates="seller", foreign_keys="[Item.seller_id]")
    bids = relationship("Bid", back_populates="bidder")

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    starting_price = Column(Float)
    current_price = Column(Float)
    end_time = Column(DateTime)
    seller_id = Column(Integer, ForeignKey("users.id"))
    highest_bidder_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String, default="active") # active, closed, paid
    shipping_time_days = Column(Integer, default=5)
    expedited_shipping_cost = Column(Float, default=15.0)

    seller = relationship("User", back_populates="items_for_sale", foreign_keys=[seller_id])
    highest_bidder = relationship("User", foreign_keys=[highest_bidder_id])
    bids = relationship("Bid", back_populates="item")

class Bid(Base):
    __tablename__ = "bids"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

    item = relationship("Item", back_populates="bids")
    bidder = relationship("User", back_populates="bids")

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    amount_paid = Column(Float)
    shipping_address = Column(String)
    expedited_shipping = Column(Boolean, default=False)
    status = Column(String, default="paid")
    created_at = Column(DateTime, default=datetime.utcnow)

from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime, timezone


# --- User Schemas ---
class UserCreate(BaseModel):
    username: str
    password: str
    first_name: str
    last_name: str
    address: str


class User(BaseModel):
    id: int
    username: str
    first_name: str
    last_name: str
    address: str

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --- Item Schemas ---
class ItemCreate(BaseModel):
    title: str
    description: str
    starting_price: float
    end_time: datetime
    shipping_time_days: Optional[int] = 5
    expedited_shipping_cost: Optional[float] = 15.0

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Title cannot be empty.")
        return v.strip()

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Description cannot be empty.")
        return v.strip()

    @field_validator("starting_price")
    @classmethod
    def price_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Starting price must be greater than zero.")
        return v

    @field_validator("end_time")
    @classmethod
    def end_time_in_future(cls, v: datetime) -> datetime:
        if v.replace(tzinfo=timezone.utc) <= datetime.now(timezone.utc):
            raise ValueError("End time must be in the future.")
        return v


class Item(BaseModel):
    id: int
    title: str
    description: str
    starting_price: float
    current_price: float
    end_time: datetime
    seller_id: int
    highest_bidder_id: Optional[int] = None
    status: str
    shipping_time_days: int
    expedited_shipping_cost: float

    class Config:
        from_attributes = True


# --- Bid Schemas ---
class BidCreate(BaseModel):
    amount: float


class Bid(BaseModel):
    id: int
    item_id: int
    user_id: int
    amount: float
    timestamp: datetime

    class Config:
        from_attributes = True


# --- Payment Schemas ---
class PaymentRequest(BaseModel):
    credit_card_number: str
    name_on_card: str
    expiration_date: str
    security_code: str
    expedited_shipping: bool = False
    shipping_address: Optional[str] = None  # If omitted, user's profile address is used


class Receipt(BaseModel):
    order_id: int
    item_id: int
    item_title: str
    amount_paid: float
    shipping_address: str
    shipping_time_days: int
    expedited_shipping: bool
    paid_at: datetime
    message: str


# --- Notification Schemas ---
class Notification(BaseModel):
    id: int
    user_id: int
    item_id: int
    message: str
    is_highest_bidder: bool
    highest_bid_amount: Optional[float] = None
    created_at: datetime
    read: bool

    class Config:
        from_attributes = True

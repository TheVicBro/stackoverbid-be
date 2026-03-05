from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


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


class ItemUpdate(BaseModel):
    """Partial update schema for UC8. Only title and description may be edited.
    Fields are optional — omitting one leaves it unchanged."""
    title: Optional[str] = None
    description: Optional[str] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Title cannot be empty.")
        return v.strip() if v else v

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Description cannot be empty.")
        return v.strip() if v else v


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

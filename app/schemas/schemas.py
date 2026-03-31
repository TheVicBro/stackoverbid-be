from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field, field_serializer, field_validator


class Link(BaseModel):
    rel: str
    href: str
    method: str


USERNAME_MIN_LENGTH = 3
PASSWORD_MIN_LENGTH = 8


class UserCreate(BaseModel):
    username: str
    password: str
    first_name: str
    last_name: str
    address: Optional[str] = ""

    @field_validator("first_name", "last_name")
    @classmethod
    def capitalize_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Name cannot be empty.")
        return v.strip().title()

    @field_validator("username")
    @classmethod
    def username_not_empty_and_min_length(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Username cannot be empty.")
        if len(v) < USERNAME_MIN_LENGTH:
            raise ValueError(f"Username must be at least {USERNAME_MIN_LENGTH} characters.")
        return v

    @field_validator("password")
    @classmethod
    def password_not_empty_and_min_length(cls, v: str) -> str:
        if not v:
            raise ValueError("Password cannot be empty.")
        if len(v) < PASSWORD_MIN_LENGTH:
            raise ValueError(f"Password must be at least {PASSWORD_MIN_LENGTH} characters.")
        return v


class User(BaseModel):
    id: int
    username: str
    first_name: str
    last_name: str
    address: str
    links: List[Link] = []

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    address: Optional[str] = None

    @field_validator("first_name", "last_name")
    @classmethod
    def names_optional(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        s = v.strip()
        if not s:
            raise ValueError("Name cannot be empty.")
        return s.title()

    @field_validator("address")
    @classmethod
    def address_optional(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return v.strip()


class UserLogin(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def username_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Username cannot be empty.")
        return v.strip()

    @field_validator("password")
    @classmethod
    def password_not_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("Password cannot be empty.")
        return v


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    links: List[Link] = []


class ItemCreate(BaseModel):
    title: str
    description: str
    starting_price: float
    end_time: datetime
    shipping_time_days: Optional[int] = 5
    expedited_shipping_cost: Optional[float] = 15.0
    image_urls: List[str] = Field(default_factory=list)

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
        # Treat naive datetimes as UTC; convert aware datetimes to UTC.
        v_utc = v.replace(tzinfo=timezone.utc) if v.tzinfo is None else v.astimezone(timezone.utc)
        if v_utc <= datetime.now(timezone.utc):
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
    image_urls: List[str] = Field(default_factory=list)
    links: List[Link] = []

    @field_validator("image_urls", mode="before")
    @classmethod
    def parse_image_urls(cls, v):
        if isinstance(v, str):
            try:
                import json
                return json.loads(v)
            except Exception:
                return []
        return v or []

    @field_serializer("end_time")
    def serialize_end_time_utc_z(self, v: datetime) -> str:
        """Naive DB times are UTC; browsers need an explicit offset or they parse as *local*."""
        aware = v.replace(tzinfo=timezone.utc) if v.tzinfo is None else v.astimezone(timezone.utc)
        return aware.isoformat(timespec="microseconds").replace("+00:00", "Z")

    class Config:
        from_attributes = True


class ItemUpdate(BaseModel):
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


class BidCreate(BaseModel):
    amount: float


class Bid(BaseModel):
    id: int
    item_id: int
    user_id: int
    amount: float
    timestamp: datetime
    links: List[Link] = []

    class Config:
        from_attributes = True


class PaymentRequest(BaseModel):
    credit_card_number: str
    name_on_card: str
    expiration_date: str
    security_code: str
    expedited_shipping: bool = False
    shipping_address: Optional[str] = None  # If omitted, user's profile address is used

    @field_validator("credit_card_number")
    @classmethod
    def validate_card_number(cls, v: str) -> str:
        cleaned = v.strip()
        digits = cleaned.replace(" ", "").replace("-", "")
        if not digits.isdigit():
            raise ValueError("Card number must contain only digits, spaces, or hyphens.")
        if len(digits) < 13 or len(digits) > 19:
            raise ValueError("Card number must be 13 to 19 digits.")
        return digits

    @field_validator("expiration_date")
    @classmethod
    def validate_expiry(cls, v: str) -> str:
        v = v.strip().replace(" ", "")
        if "/" in v:
            parts = v.split("/")
        elif "-" in v:
            parts = v.split("-")
        else:
            raise ValueError("Expiration must be MM/YY or MM-YY.")
        if len(parts) != 2:
            raise ValueError("Expiration must be MM/YY or MM-YY.")
        if len(parts[0]) != 2 or len(parts[1]) != 2:
            raise ValueError("Expiration must be MM/YY or MM-YY (two digits each).")
        try:
            month, year = int(parts[0]), int(parts[1])
        except ValueError:
            raise ValueError("Expiration must be MM/YY or MM-YY.")
        if month < 1 or month > 12:
            raise ValueError("Month must be 01-12.")
        full_year = 2000 + year
        now = datetime.now(timezone.utc)
        if full_year < now.year or (full_year == now.year and month < now.month):
            raise ValueError("Card has expired.")
        return v

    @field_validator("security_code")
    @classmethod
    def validate_cvv(cls, v: str) -> str:
        v = v.strip()
        if not v.isdigit():
            raise ValueError("Security code must contain only digits.")
        if len(v) not in (3, 4):
            raise ValueError("Security code must be 3 or 4 digits.")
        return v

    @field_validator("name_on_card")
    @classmethod
    def name_on_card_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Name on card cannot be empty.")
        return v.strip()


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
    links: List[Link] = []


class Notification(BaseModel):
    id: int
    user_id: int
    item_id: int
    message: str
    is_highest_bidder: bool
    highest_bid_amount: Optional[float] = None
    created_at: datetime
    read: bool
    links: List[Link] = []

    class Config:
        from_attributes = True


class BroadcastEndResponse(BaseModel):
    message: str
    links: List[Link] = []

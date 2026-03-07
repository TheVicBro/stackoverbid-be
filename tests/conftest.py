from datetime import datetime, timedelta, timezone
from typing import Optional

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.models import Bid, Item, User
from app.utils.auth import hash_password, access_token

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db):
    def _override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def create_user(db):
    def _create(
        username: str = "testuser",
        password: str = "password123",
        first_name: str = "Test",
        last_name: str = "User",
        address: str = "123 Test St",
    ):
        user = User(
            username=username,
            hashed_password=hash_password(password),
            first_name=first_name,
            last_name=last_name,
            address=address,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        token = access_token(data={"sub": str(user.id), "username": user.username})
        return user, token

    return _create


@pytest.fixture()
def create_item(db):
    def _create(
        seller_id: int,
        title: str = "Test Item",
        description: str = "Test description",
        starting_price: float = 10.0,
        current_price: Optional[float] = None,
        status: str = "active",
        end_time: Optional[datetime] = None,
        shipping_time_days: int = 5,
        expedited_shipping_cost: float = 15.0,
        highest_bidder_id: Optional[int] = None,
    ):
        if end_time is None:
            end_time = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=2)
        if current_price is None:
            current_price = starting_price
        item = Item(
            title=title,
            description=description,
            starting_price=starting_price,
            current_price=current_price,
            end_time=end_time,
            seller_id=seller_id,
            status=status,
            shipping_time_days=shipping_time_days,
            expedited_shipping_cost=expedited_shipping_cost,
            highest_bidder_id=highest_bidder_id,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    return _create


@pytest.fixture()
def create_bid(db):
    def _create(item_id: int, user_id: int, amount: float):
        bid = Bid(item_id=item_id, user_id=user_id, amount=amount)
        db.add(bid)
        db.commit()
        db.refresh(bid)
        return bid

    return _create


VALID_PAYMENT = {
    "credit_card_number": "4111111111111111",
    "name_on_card": "Test User",
    "expiration_date": "12/30",
    "security_code": "123",
    "expedited_shipping": False,
}


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}

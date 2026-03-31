from typing import Optional

from sqlalchemy.orm import Session

from app.models import models
from app.schemas import schemas


def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()


def create_user(db: Session, user_in: schemas.UserCreate, hashed_password: str) -> models.User:
    db_user = models.User(
        username=user_in.username,
        hashed_password=hashed_password,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        address=user_in.address,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user_profile(db: Session, user: models.User, data: schemas.UserUpdate) -> models.User:
    patch = data.model_dump(exclude_unset=True)
    if "first_name" in patch:
        user.first_name = patch["first_name"]
    if "last_name" in patch:
        user.last_name = patch["last_name"]
    if "address" in patch:
        user.address = patch["address"]
    db.commit()
    db.refresh(user)
    return user


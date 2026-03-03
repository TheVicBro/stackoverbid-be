from typing import Optional

from sqlalchemy.orm import Session  # type: ignore[import]

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


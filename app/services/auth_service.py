from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.utils import auth
from app.daos import user_dao
from app.schemas import schemas


def signup(db: Session, user_in: schemas.UserCreate) -> schemas.User:
    existing = user_dao.get_user_by_username(db, user_in.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed = auth.hash_password(user_in.password)
    user = user_dao.create_user(db, user_in, hashed)
    return schemas.User.model_validate(user)


def login(db: Session, credentials: schemas.UserLogin) -> schemas.Token:
    user = user_dao.get_user_by_username(db, credentials.username)
    if not user or not auth.verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid username or password")
    access_token = auth.access_token(data={"sub": str(user.id), "username": user.username})
    return schemas.Token(access_token=access_token)


def update_profile(db: Session, user_id: int, data: schemas.UserUpdate) -> schemas.User:
    patch = data.model_dump(exclude_unset=True)
    if not patch:
        raise HTTPException(status_code=400, detail="No fields to update.")
    user = user_dao.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    user_dao.update_user_profile(db, user, data)
    return schemas.User.model_validate(user)


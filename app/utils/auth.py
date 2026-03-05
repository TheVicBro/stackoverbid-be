from typing import Optional

from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import models

ALGORITHM = "HS256"
SECRET_KEY = "examplekey"
ctx = CryptContext(schemes=["bcrypt_sha256"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    return ctx.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return ctx.verify(plain_password, hashed_password)


def access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=(60 * 24)))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    """Decode the JWT and return the authenticated User ORM object.

    Raises 401 if the token is invalid, expired, or the user no longer exists.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise credentials_exception

    from app.daos import user_dao  # local import to avoid circular dependency

    user = user_dao.get_user_by_id(db, user_id)
    if user is None:
        raise credentials_exception
    return user
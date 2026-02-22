from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta, timezone

SECRET_KEY = "examplekey"
ctx = CryptContext(schemes=["bcrypt_sha256"])

def hash_password(password: str) -> str:
    return ctx.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return ctx.verify(plain_password, hashed_password)

def access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=(60*24)))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
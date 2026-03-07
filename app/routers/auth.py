from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import schemas
from app.services import auth_service

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

@router.post("/signup", response_model=schemas.User)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    result = auth_service.signup(db, user)
    result.links = [
        schemas.Link(rel="login", href="/auth/login", method="POST"),
    ]
    return result

@router.post("/login", response_model=schemas.Token)
def login(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    result = auth_service.login(db, credentials)
    result.links = [
        schemas.Link(rel="catalogue", href="/catalogue/items", method="GET"),
        schemas.Link(rel="create_item", href="/auction/items", method="POST"),
        schemas.Link(rel="notifications", href="/notifications/", method="GET"),
    ]
    return result

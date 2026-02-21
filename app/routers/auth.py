from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import models
from app.schemas import schemas

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

@router.post("/signup", response_model=schemas.User)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Skeleton: Just save the user directly (No password hashing for now)
    db_user = models.User(
        username=user.username,
        hashed_password=user.password, # Storing plain text for skeleton
        first_name=user.first_name,
        last_name=user.last_name,
        address=user.address
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/login")
def login():
    # Skeleton: Placeholder for login logic
    return {"message": "Login endpoint skeleton"}

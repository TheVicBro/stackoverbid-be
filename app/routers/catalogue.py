from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import models
from app.schemas import schemas

router = APIRouter(
    prefix="/catalogue",
    tags=["catalogue"]
)

@router.get("/items", response_model=List[schemas.Item])
def get_items(db: Session = Depends(get_db)):
    # Skeleton: Return all items
    return db.query(models.Item).all()

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import models
from app.schemas import schemas
from typing import List, Optional

router = APIRouter(
    prefix="/catalogue",
    tags=["catalogue"]
)

@router.get("/items", response_model=List[schemas.Item])
def get_items(
    db: Session = Depends(get_db), 
    keyword: Optional[str] = None, 
):
    query = db.query(models.Item)
    
    query = query.filter(models.Item.status == "active")
    
    if keyword:
        pattern = f"%{q}%"
        query = query.filter(models.Item.title.ilike(pattern)) 
    
    return query.all()
        

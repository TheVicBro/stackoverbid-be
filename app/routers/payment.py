from fastapi import APIRouter, Depends  # type: ignore[import]
from sqlalchemy.orm import Session  # type: ignore[import]

from app.database import get_db
from app.models import models
from app.schemas import schemas
from app.services import payment_service
from app.utils.auth import get_current_user


router = APIRouter(
    prefix="/payment",
    tags=["payment"],
)


@router.post("/items/{item_id}/pay")
def process_payment(
    item_id: int,
    payment: schemas.PaymentRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """UC5 – The winning bidder pays for the item."""
    order = payment_service.process_payment(
        db, item_id=item_id, user_id=current_user.id, payment=payment
    )
    return {"message": f"Payment processed for item {item_id}", "order_id": order.id}

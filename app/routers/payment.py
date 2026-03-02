from fastapi import APIRouter, Depends  # type: ignore[import]
from sqlalchemy.orm import Session  # type: ignore[import]

from app.database import get_db
from app.schemas import schemas
from app.services import payment_service


router = APIRouter(
    prefix="/payment",
    tags=["payment"],
)


@router.post("/items/{item_id}/pay")
def process_payment(
    item_id: int,
    payment: schemas.PaymentRequest,
    db: Session = Depends(get_db),
):
    # For now we use a hardcoded user_id; later this should come from auth.
    order = payment_service.process_payment(db, item_id=item_id, user_id=1, payment=payment)
    return {"message": f"Payment processed for item {item_id}", "order_id": order.id}

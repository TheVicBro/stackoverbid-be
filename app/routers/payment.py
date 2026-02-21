from fastapi import APIRouter
from app.schemas import schemas

router = APIRouter(
    prefix="/payment",
    tags=["payment"]
)

@router.post("/items/{item_id}/pay")
def process_payment(item_id: int, payment: schemas.PaymentRequest):
    # Skeleton: Placeholder for payment logic
    return {"message": f"Payment processed for item {item_id}"}

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.database import get_db
from app.events import AuctionClosedEvent, AuctionClosedNotificationPayload, auction_closed_subject
from app.models import models
from app.pubsub import pubsub
from app.schemas import schemas
from app.services import notification_service
from app.utils.auth import get_current_user, get_user_from_token


router = APIRouter(
    prefix="/notifications",
    tags=["notifications"],
)


@router.websocket("/ws/{user_id}")
async def websocket_notifications(
    websocket: WebSocket,
    user_id: int,
    db: Session = Depends(get_db),
) -> None:
    # Require JWT and ensure the caller can only subscribe to their own topic.
    token: Optional[str] = None
    auth_header = websocket.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1].strip()
    else:
        token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        current_user = get_user_from_token(db, token)
    except (HTTPException, JWTError):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    if current_user.id != user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    topic = f"user:{current_user.id}"

    async def send(message: dict) -> None:
        await websocket.send_json(message)

    pubsub.subscribe(topic, send)
    try:
        while True:
            # Keep the connection alive; client messages are ignored for now
            await websocket.receive_text()
    except WebSocketDisconnect:
        pubsub.unsubscribe(topic, send)


@router.get("/", response_model=List[schemas.Notification])
def list_notifications(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> List[schemas.Notification]:
    """Return notifications for the authenticated user."""
    notifications = notification_service.list_notifications_for_user(db, current_user.id)
    return [schemas.Notification.model_validate(n) for n in notifications]


@router.post("/items/{item_id}/broadcast-end")
async def broadcast_auction_end(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> dict:
    from app.daos import item_dao

    item = item_dao.get_item(db, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found.")
    if item.seller_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the seller can close their auction.")
    notifications_to_send = notification_service.close_auction_and_create_notifications(db, item_id)

    # Observer pattern: notify observers (e.g. BroadcastToWebSocketObserver pushes via pub-sub)
    event = AuctionClosedEvent(
        notifications=[
            AuctionClosedNotificationPayload(
                notification_id=n.id,
                user_id=n.user_id,
                item_id=n.item_id,
                message=n.message,
                is_highest_bidder=n.is_highest_bidder,
                highest_bid_amount=n.highest_bid_amount,
            )
            for n in notifications_to_send
        ]
    )
    await auction_closed_subject.notify(event)

    return {"message": "Notifications broadcast to all bidders"}


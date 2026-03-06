from typing import Awaitable, Callable, Dict, List, Optional, Set

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import models
from app.schemas import schemas
from app.services import notification_service
from app.utils.auth import get_current_user, get_user_from_token


router = APIRouter(
    prefix="/notifications",
    tags=["notifications"],
)


Subscriber = Callable[[dict], Awaitable[None]]


class InMemoryPubSub:
    def __init__(self) -> None:
        # topic -> set of async callbacks
        self._subscribers: Dict[str, Set[Subscriber]] = {}

    def subscribe(self, topic: str, callback: Subscriber) -> None:
        self._subscribers.setdefault(topic, set()).add(callback)

    def unsubscribe(self, topic: str, callback: Subscriber) -> None:
        callbacks = self._subscribers.get(topic)
        if not callbacks:
            return
        callbacks.discard(callback)
        if not callbacks:
            self._subscribers.pop(topic, None)

    async def publish(self, topic: str, message: dict) -> None:
        callbacks = list(self._subscribers.get(topic, set()))
        for callback in callbacks:
            try:
                await callback(message)
            except WebSocketDisconnect:
                # Disconnection is handled by the websocket endpoint loop
                continue


pubsub = InMemoryPubSub()


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
    result = []
    for n in notifications:
        notif = schemas.Notification.model_validate(n)
        notif.links = [
            schemas.Link(rel="item", href=f"/catalogue/items/{notif.item_id}", method="GET"),
        ]
        if notif.is_highest_bidder:
            notif.links.append(
                schemas.Link(rel="pay", href=f"/payment/items/{notif.item_id}/pay", method="POST")
            )
        result.append(notif)
    return result


@router.post("/items/{item_id}/broadcast-end", response_model=schemas.BroadcastEndResponse)
async def broadcast_auction_end(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> schemas.BroadcastEndResponse:
    from app.daos import item_dao

    item = item_dao.get_item(db, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found.")
    if item.seller_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the seller can close their auction.")
    notifications_to_send = notification_service.close_auction_and_create_notifications(db, item_id)

    for notification in notifications_to_send:
        payload = {
            "notification_id": notification.id,
            "item_id": notification.item_id,
            "message": notification.message,
            "is_highest_bidder": notification.is_highest_bidder,
            "highest_bid_amount": notification.highest_bid_amount,
            "can_proceed_to_payment": notification.is_highest_bidder,
            "payment_url": f"/payment/items/{notification.item_id}/pay" if notification.is_highest_bidder else None,
        }
        await pubsub.publish(f"user:{notification.user_id}", payload)

    return schemas.BroadcastEndResponse(
        message="Notifications broadcast to all bidders",
        links=[
            schemas.Link(rel="item", href=f"/catalogue/items/{item_id}", method="GET"),
            schemas.Link(rel="notifications", href="/notifications/", method="GET"),
        ],
    )


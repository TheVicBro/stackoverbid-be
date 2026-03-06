"""
Observer pattern: domain events with multiple observers.
Subject notifies observers when something happens; each observer reacts (e.g. persist, broadcast).
Pub-Sub (app.pubsub) remains the transport for pushing to WebSocket clients; observers may use it.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from app.pubsub import InMemoryPubSub, pubsub


# --- Domain event (payload for observers) ---
@dataclass
class AuctionClosedNotificationPayload:
    """Data for one notification when an auction closes."""
    notification_id: int
    user_id: int
    item_id: int
    message: str
    is_highest_bidder: bool
    highest_bid_amount: float | None


@dataclass
class AuctionClosedEvent:
    """Emitted when an auction is closed and notifications were created."""
    notifications: List[AuctionClosedNotificationPayload]


# --- Observer interface ---
class AuctionClosedObserver(ABC):
    @abstractmethod
    async def on_auction_closed(self, event: AuctionClosedEvent) -> None:
        """Called when an auction has been closed and notifications created."""
        pass


# --- Subject: holds observers and notifies them ---
class AuctionClosedSubject:
    def __init__(self) -> None:
        self._observers: List[AuctionClosedObserver] = []

    def attach(self, observer: AuctionClosedObserver) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer: AuctionClosedObserver) -> None:
        if observer in self._observers:
            self._observers.remove(observer)

    async def notify(self, event: AuctionClosedEvent) -> None:
        for observer in self._observers:
            await observer.on_auction_closed(event)


# --- Concrete observer: pushes to WebSocket clients via Pub-Sub ---
class BroadcastToWebSocketObserver(AuctionClosedObserver):
    """Observes auction-closed events and broadcasts each notification to the user's WebSocket topic."""

    def __init__(self, pubsub_instance: InMemoryPubSub) -> None:
        self._pubsub = pubsub_instance

    async def on_auction_closed(self, event: AuctionClosedEvent) -> None:
        for n in event.notifications:
            payload = {
                "notification_id": n.notification_id,
                "item_id": n.item_id,
                "message": n.message,
                "is_highest_bidder": n.is_highest_bidder,
                "highest_bid_amount": n.highest_bid_amount,
                "can_proceed_to_payment": n.is_highest_bidder,
                "payment_url": f"/payment/items/{n.item_id}/pay" if n.is_highest_bidder else None,
            }
            await self._pubsub.publish(f"user:{n.user_id}", payload)


# Singleton subject and registration
auction_closed_subject = AuctionClosedSubject()
auction_closed_subject.attach(BroadcastToWebSocketObserver(pubsub))

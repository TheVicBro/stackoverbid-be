"""
Pub-Sub: decoupled message delivery to topics (e.g. WebSocket clients).
Used for real-time push; observers (see events.py) may publish to this.
"""
from typing import Awaitable, Callable, Dict, Set

from fastapi import WebSocketDisconnect

Subscriber = Callable[[dict], Awaitable[None]]


class InMemoryPubSub:
    def __init__(self) -> None:
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
                continue


pubsub = InMemoryPubSub()

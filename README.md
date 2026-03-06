# StackOverbid Backend

StackOverbid is an auction e-commerce system backend built with Python and FastAPI. It provides a modular skeleton for handling user authentication, item cataloging, bidding, and payment processing.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Setup and Installation

Follow these steps to set up the project locally. Instructions are provided for both Windows and macOS/Linux.

### 1. Clone the repository (if applicable)

```bash
git clone <your-repository-url>
cd stackoverbid-be
```

### 2. Create a Virtual Environment

It is highly recommended to use a virtual environment to manage dependencies.

**On Windows:**
```powershell
python -m venv venv
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

Once your virtual environment is activated, install the required packages:

```bash
pip install -r requirements.txt
```

## Running the Application

Start the FastAPI development server using Uvicorn:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

## How to Use

Once the server is running, you can interact with the API using the built-in interactive documentation:

- **Swagger UI (Recommended):** Navigate to [http://localhost:8000/docs](http://localhost:8000/docs) in your browser. This interface allows you to explore all available endpoints, see required parameters, and test API calls directly.
- **ReDoc:** Alternatively, you can view the documentation at [http://localhost:8000/redoc](http://localhost:8000/redoc).

### Project Structure

- `app/main.py`: The entry point of the application.
- `app/routers/`: Contains the API endpoints (Auth, Auction, Catalogue, Payment, Notifications).
- `app/models/`: SQLAlchemy database models.
- `app/schemas/`: Pydantic schemas for data validation.
- `app/database.py`: Database connection and session management (using SQLite).
- `app/daos/`: Data access objects (persistence).
- `app/services/`: Business logic.
- `app/events.py`: Domain events and **Observer** pattern.
- `app/pubsub.py`: **Pub-Sub** for real-time WebSocket delivery.
- `app/strategies/`: **Strategy** pattern (e.g. shipping cost).
- `app/repositories/`: **Repository** pattern (abstract data access).

## Design Patterns
# StackOverbid Backend

StackOverbid is an auction e-commerce system backend built with Python and FastAPI. It provides a modular skeleton for handling user authentication, item cataloging, bidding, and payment processing.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Setup and Installation

Follow these steps to set up the project locally. Instructions are provided for both Windows and macOS/Linux.

### 1. Clone the repository (if applicable)

```bash
git clone <your-repository-url>
cd stackoverbid-be
```

### 2. Create a Virtual Environment

It is highly recommended to use a virtual environment to manage dependencies.

**On Windows:**
```powershell
python -m venv venv
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

Once your virtual environment is activated, install the required packages:

```bash
pip install -r requirements.txt
```

## Running the Application

Start the FastAPI development server using Uvicorn:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

## How to Use

Once the server is running, you can interact with the API using the built-in interactive documentation:

- **Swagger UI (Recommended):** Navigate to [http://localhost:8000/docs](http://localhost:8000/docs) in your browser. This interface allows you to explore all available endpoints, see required parameters, and test API calls directly.
- **ReDoc:** Alternatively, you can view the documentation at [http://localhost:8000/redoc](http://localhost:8000/redoc).

### Project Structure

- `app/main.py`: The entry point of the application.
- `app/routers/`: Contains the API endpoints (Auth, Auction, Catalogue, Payment, Notifications).
- `app/models/`: SQLAlchemy database models.
- `app/schemas/`: Pydantic schemas for data validation.
- `app/database.py`: Database connection and session management (using SQLite).
- `app/daos/`: Data access objects (persistence).
- `app/services/`: Business logic.
- `app/events.py`: Domain events and **Observer** pattern.
- `app/pubsub.py`: **Pub-Sub** for real-time WebSocket delivery.
- `app/strategies/`: **Strategy** pattern (e.g. shipping cost).
- `app/repositories/`: **Repository** pattern (abstract data access).

## Design Patterns

The codebase uses four design patterns to keep concerns separated and make the system easier to extend and test. Below is a more detailed explanation of how each one works.

### Observer (in detail)

The Observer pattern lets one part of the system announce that something happened, and other parts react without the announcer knowing who they are. There are three roles: the **subject** (who holds the list of observers and notifies them), the **observers** (who implement a common interface and do something when notified), and the **event** (the data passed when something happens).

In this codebase the subject is `AuctionClosedSubject` in `app/events.py`. It keeps a list of observers and exposes `attach(observer)` and `detach(observer)` to add or remove them. When `notify(event)` is called, it loops over that list and calls each observer's `on_auction_closed(event)` method. The event is an `AuctionClosedEvent`: a small object that carries a list of `AuctionClosedNotificationPayload` (one per user to notify, with fields like `user_id`, `item_id`, `message`, `is_highest_bidder`, etc.). The code that closes the auction (the notification router) doesn't call WebSocket or any other side effect directly; it only builds this event and calls `auction_closed_subject.notify(event)`.

Each observer implements the `AuctionClosedObserver` interface: a single async method `on_auction_closed(self, event)`. At startup, one observer is attached: `BroadcastToWebSocketObserver`. When it receives an event, it iterates over `event.notifications` and, for each one, calls `pubsub.publish("user:{user_id}", payload)`. So the actual push to WebSockets is done by this observer using Pub-Sub; the router doesn't know about WebSockets at all. To add another reaction (e.g. write to a log, send an email, or update analytics), you implement another class with `on_auction_closed`, attach it to `auction_closed_subject`, and the existing flow will call it automatically whenever an auction is closed.

### Pub-Sub (in detail)

Publish–Subscribe decouples who produces a message from who consumes it by introducing a broker and topics. Producers publish to a topic; consumers subscribe to a topic; the broker delivers every message published on a topic to all its current subscribers. Producers and subscribers don't reference each other.

Here the broker is `InMemoryPubSub` in `app/pubsub.py`. Internally it holds a dictionary: topic name to set of subscriber callbacks. Each callback is an async function that takes a single `dict` (the message). `subscribe(topic, callback)` adds that callback to the topic's set; `unsubscribe(topic, callback)` removes it. `publish(topic, message)` takes the topic and a message dict, gets the set of callbacks for that topic, and awaits each callback with that message. So any code that has a reference to the broker can publish to a topic without knowing how many subscribers there are or what they do (e.g. send over a WebSocket, write to a queue, or log).

The main use is WebSocket delivery. In the notification router, when a client connects to the WebSocket endpoint, the server authenticates them, then calls `pubsub.subscribe("user:{user_id}", send)`, where `send` is an async function that forwards the message to that client's WebSocket. So the topic is effectively "messages for user X." When later something (e.g. the `BroadcastToWebSocketObserver`) calls `pubsub.publish("user:123", payload)`, the broker invokes every callback subscribed to "user:123"—in practice, the callback that sends to that user's WebSocket—so the client receives the payload in real time. When the client disconnects, the endpoint calls `unsubscribe` so that callback is removed. The publisher never sees sessions or WebSockets; it only sees "publish to this topic."

### Strategy (in detail)

The Strategy pattern replaces conditional logic (e.g. if standard vs expedited) with interchangeable algorithm objects. The caller depends on an interface and calls one method; the implementation of that method varies by strategy. To support a new variant you add a new strategy class instead of editing the caller.

Here the "algorithm" is "how much extra shipping cost to add for this item." The interface is `ShippingCostStrategy` in `app/strategies/shipping.py`, with a single method `get_shipping_cost(item) -> float`. Two classes implement it: `StandardShippingStrategy` (always returns `0.0`) and `ExpeditedShippingStrategy` (returns `item.expedited_shipping_cost`). The payment service doesn't contain an `if expedited: ... else: ...`; it only does: choose the strategy (e.g. `ExpeditedShippingStrategy()` if the request asks for expedited, else `StandardShippingStrategy()`), then compute `amount_paid = item.current_price + shipping_strategy.get_shipping_cost(item)`. The rest of the payment flow (validation, creating the order, updating item status) is unchanged. If you add a new option (e.g. "express" or "international"), you add a new strategy class that returns the right amount and, in one place, you decide which strategy to use; the payment logic itself stays the same.

### Repository (in detail)

The Repository pattern hides the details of how entities are stored and loaded. Callers use an abstract interface (e.g. "get item by id," "save this item") instead of talking to the database or DAO directly. The concrete implementation can use SQLAlchemy, another database, or an in-memory store; the caller's code doesn't change.

Here the abstraction is `ItemRepository`, defined as a Protocol in `app/repositories/item_repository.py`. It describes four operations: `get_item(item_id)`, `create_item(item_in, seller_id)`, `update_item(item, update_in)`, and `list_active_items(keyword)`. The concrete implementation is `SqlAlchemyItemRepository`: it takes a database session in its constructor and, for each method, delegates to the existing item DAO (e.g. `item_dao.get_item(self._db, item_id)`). So the DAO still does the real work; the repository is a thin wrapper that matches the interface.

The payment router and service use this interface instead of the DAO. FastAPI's dependency injection provides it: a dependency `get_item_repository` (in `app/deps.py`) takes a session from `get_db` and returns `SqlAlchemyItemRepository(db)`. The payment endpoint declares `item_repo: ItemRepository = Depends(get_item_repository)` and passes `item_repo` into the payment service. The service then calls `item_repo.get_item(item_id)` and `item_repo.get_item(order.item_id)` instead of `item_dao.get_item(db, ...)`. So the service never imports the DAO or the database; it only sees "something that can fetch and update items." In tests you can provide a different implementation (e.g. in-memory or mock) that satisfies the same Protocol, and the same service code works without touching the database.

---

**Observer** is used for domain events such as “auction closed.” When an auction is closed, the service creates notifications in the database and then raises an `AuctionClosedEvent`. A subject (`AuctionClosedSubject`) holds a list of observers and calls each one when `notify(event)` is invoked. One observer, `BroadcastToWebSocketObserver`, takes the event and pushes each notification to the right user’s WebSocket by publishing to the Pub-Sub broker. The producer (the router or service) does not need to know who reacts—only that the event occurred. New behaviour (e.g. logging, analytics, or email) can be added by implementing the observer interface and attaching it to the subject. Observer answers *who* reacts to the event; Pub-Sub answers *how* messages reach connected clients, and the broadcast observer connects the two.

**Pub-Sub** provides decoupled, topic-based message delivery. An in-memory broker (`InMemoryPubSub` in `app/pubsub.py`) maintains topics (e.g. `user:123`) and a set of subscribers per topic. When a client opens a WebSocket, the server subscribes that connection to the topic for that user. Any code that calls `pubsub.publish("user:123", payload)` sends the payload to every subscriber of that topic—typically that user’s WebSocket—without the publisher knowing who is subscribed. This keeps real-time push flexible and independent of the code that triggers it (such as the Observer above).

**Strategy** is used for shipping cost. The payment flow needs to add a shipping cost to the item price, but the rule varies: standard shipping adds nothing, expedited adds the item’s expedited cost. Instead of branching in the payment service, we define a `ShippingCostStrategy` interface with `get_shipping_cost(item)`, and two implementations: `StandardShippingStrategy` (returns zero) and `ExpeditedShippingStrategy` (returns the item’s expedited fee). The payment service picks the strategy based on the request and computes `amount_paid = item.current_price + strategy.get_shipping_cost(item)`. New shipping types can be added as new strategy classes without changing the payment logic.

**Repository** hides how items are stored behind an abstract `ItemRepository` interface (e.g. `get_item`, `create_item`, `update_item`, `list_active_items`). The concrete implementation, `SqlAlchemyItemRepository`, delegates to the existing item DAO. The payment router injects an `ItemRepository` via FastAPI’s `Depends(get_item_repository)`, and the payment service uses `item_repo.get_item(item_id)` instead of calling the DAO directly. Services then depend on the abstraction, not on SQLAlchemy or the DAO, so tests can inject an in-memory or mock repository and the same code can later use a different storage implementation.

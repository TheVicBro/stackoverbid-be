# StackOverbid Backend

FastAPI backend for StackOverbid, an auction marketplace: auth, catalogue, bidding, auction close, notifications, and in-app checkout.

**Frontend:** [TheVicBro/stackoverbid](https://github.com/TheVicBro/stackoverbid) · **Live app:** [stackoverbid.vercel.app](https://stackoverbid.vercel.app)

Team course project. “Payment” creates an order and receipt in the database (winner-only, shipping strategy). There is no Stripe/PayPal integration.

## Architecture

- **Routers** stay thin; **services** own bid rules, auction finalization, and checkout.
- **DAOs** isolate SQLAlchemy queries.
- Bidding rejects seller self-bids and amounts at or below the current price; listings cannot be edited after a bid or after expiry.
- Expired auctions are closed on demand (notifications for bidders; winner can pay).
- Optional Gemini tag suggestions for new listings; keyword heuristics if `GEMINI_API_KEY` is unset.
- SQLite locally, Postgres in production (`DATABASE_URL`). JWT via `SECRET_KEY`.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Setup and Installation

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd stackoverbid-be
```

### 2. Create a virtual environment

**Windows:**
```powershell
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and set a secure `SECRET_KEY` (used for JWT signing).

## Running the Application

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

### Seed the database (optional)

Populate the database with sample users, items, bids, and notifications:

```bash
python -m scripts.seed_db
```

This creates three test accounts (`alice`, `bob`, `carol`, all with password `password123`).

## API Documentation

Once the server is running:

- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Running Tests

### Unit / integration tests (pytest)

```bash
pytest tests/ --tb=short
```

Tests cover authentication, catalogue, bidding, auction lifecycle, payment, receipts, notifications, schema validation, and HATEOAS links. Tests use an in-memory SQLite database and are fully isolated.

### Curl scripts

Two bash scripts exercise the API:

**Main flow** — walks through the complete auction lifecycle (UC1–UC8):

```bash
bash scripts/curl_main_flow.sh
```

**Robustness tests** — wrong inputs, authorization failures, business rule violations:

```bash
bash scripts/curl_robustness_tests.sh
```

> **Prerequisites:** the server must be running and the database must be fresh (delete `stackoverbid.db` before running). Run `curl_main_flow.sh` first, then `curl_robustness_tests.sh`.

## Project Structure

```
app/
  main.py                 - Application entry point
  database.py             - Database connection and session management (SQLite)
  models/models.py        - SQLAlchemy ORM models
  schemas/schemas.py      - Pydantic request/response schemas with validators
  routers/
    auth.py               - Sign up, login (JWT)
    catalogue.py          - Browse / search items, view item details
    auction.py            - Create item, edit item, place bid
    notification.py       - List notifications, broadcast auction end
    payment.py            - Pay for won item, view receipt
  services/
    auth_service.py
    auction_service.py
    catalogue_service.py
    notification_service.py
    payment_service.py
    shipping_strategy.py  - Strategy pattern for shipping
  daos/
    user_dao.py
    item_dao.py
    bid_dao.py
    order_dao.py
    notification_dao.py
  utils/auth.py           - JWT utilities, password hashing
scripts/
  seed_db.py              - Database seeder
  curl_main_flow.sh       - Curl script: full auction lifecycle (UC1-UC8)
  curl_robustness_tests.sh - Curl script: edge cases and error handling
tests/                    - pytest test cases
```

## Design Patterns

- **DAO** (`app/daos/`) - Each model has a dedicated DAO isolating database queries from business logic.
- **Service Layer** (`app/services/`) - Services encapsulate business rules and orchestrate DAO calls; routers stay thin.
- **Pub-Sub** (`app/services/notification_service.py`) - `InMemoryPubSub` broadcasts auction-end notifications to all bidders.
- **Strategy** (`app/services/shipping_strategy.py`) - Interchangeable `StandardShipping` / `ExpeditedShipping` algorithms behind a common interface, selected at runtime by the payment service.

## HATEOAS

All API responses include contextual `links` (rel, href, method) guiding the client to related actions. For example, a winning notification includes a link to the payment endpoint.

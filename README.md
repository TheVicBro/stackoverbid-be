# StackOverbid Backend

StackOverbid is an auction e-commerce system backend built with Python and FastAPI. It supports user authentication, item cataloging, real-time bidding, notifications, and payment processing with receipt generation.

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

This creates three test accounts (`alice`, `bob`, `carol` — all with password `password123`).

## API Documentation

Once the server is running:

- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Running Tests

### Unit / integration tests (pytest)

```bash
pytest tests/ --tb=short
```

106 tests covering authentication, catalogue, bidding, auction lifecycle, payment, receipts, notifications, schema validation, and HATEOAS links. Tests use an in-memory SQLite database and are fully isolated.

### Curl script

A bash script exercises the full API flow (happy path + robustness checks):

```bash
bash scripts/curl_tests.sh
```

> **Prerequisites:** the server must be running and the database must be fresh (delete `stackoverbid.db` before running).

## Project Structure

```
app/
├── main.py              # Application entry point
├── database.py          # Database connection and session management (SQLite)
├── models/models.py     # SQLAlchemy ORM models
├── schemas/schemas.py   # Pydantic request/response schemas with validators
├── routers/             # API endpoint handlers
│   ├── auth.py          # Sign up, login (JWT)
│   ├── catalogue.py     # Browse / search items, view item details
│   ├── auction.py       # Create item, edit item, place bid
│   ├── notification.py  # List notifications, broadcast auction end
│   └── payment.py       # Pay for won item, view receipt
├── services/            # Business logic layer
│   ├── auth_service.py
│   ├── auction_service.py
│   ├── catalogue_service.py
│   ├── notification_service.py
│   ├── payment_service.py
│   └── shipping_strategy.py # Strategy pattern for shipping
├── daos/                # Data Access Objects (DAO pattern)
│   ├── user_dao.py
│   ├── item_dao.py
│   ├── bid_dao.py
│   ├── order_dao.py
│   └── notification_dao.py
└── utils/auth.py        # JWT utilities, password hashing
scripts/
├── seed_db.py           # Database seeder
└── curl_tests.sh        # Curl-based API test script
tests/                   # 106 pytest test cases
```

## Design Patterns

| Pattern | Where | Description |
|---|---|---|
| **DAO** | `app/daos/` | Each model has a dedicated DAO isolating database queries from business logic. |
| **Service Layer** | `app/services/` | Services encapsulate business rules and orchestrate DAO calls; routers stay thin. |
| **Pub-Sub** | `app/services/notification_service.py` | `InMemoryPubSub` broadcasts auction-end notifications to all bidders. |
| **Strategy** | `app/services/shipping_strategy.py` | Interchangeable `StandardShipping` / `ExpeditedShipping` algorithms behind a common interface, selected at runtime by the payment service. |

## HATEOAS

All API responses include contextual `links` (rel, href, method) guiding the client to related actions. For example, a winning notification includes a link to the payment endpoint.

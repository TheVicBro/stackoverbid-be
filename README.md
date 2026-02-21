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
- `app/routers/`: Contains the API endpoints (Auth, Auction, Catalogue, Payment).
- `app/models/`: SQLAlchemy database models.
- `app/schemas/`: Pydantic schemas for data validation.
- `app/database.py`: Database connection and session management (using SQLite).

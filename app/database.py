import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Fetch database URL from environment variable, falling back to local SQLite
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./stackoverbid.db")

# SQLAlchemy requires postgresql:// instead of postgres:// 
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLite needs connect_args for multithreading, Postgres does not
connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}

is_postgres = not SQLALCHEMY_DATABASE_URL.startswith("sqlite")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=connect_args,
    # Pre-ping checks the connection before use; discards stale ones so the
    # pool never hands a dead SSL connection to a request.
    pool_pre_ping=is_postgres,
    # Recycle connections older than 10 minutes to stay ahead of the
    # server-side idle timeout on Neon / Render managed Postgres.
    pool_recycle=600 if is_postgres else -1,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

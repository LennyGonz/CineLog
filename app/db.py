import os
from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Add it to .env")

# For psycopg3 + SQLAlchemy 2.x, set sslmode only when needed.
connect_args = {}
if "sslmode=" not in DATABASE_URL:
    if "localhost" in DATABASE_URL or "127.0.0.1" in DATABASE_URL:
        connect_args = {}
    else:
        connect_args = {"sslmode": "require"}

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # helps avoid stale connections
    connect_args=connect_args,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Session:
    """
    FastAPI dependency that provides a SQLAlchemy session per request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

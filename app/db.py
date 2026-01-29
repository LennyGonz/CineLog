import os
from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Add it to .env")

# For psycopg3 + SQLAlchemy 2.x, this is fine.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # helps avoid stale connections
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

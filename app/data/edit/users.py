"""
Edit operations for User entity.
"""

from sqlalchemy.orm import Session
from uuid import UUID
from app.models import User


def create_or_get_user(db: Session, email: str) -> User:
    """Create a user if not exists, otherwise return existing user."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email)
        db.add(user)
        db.flush()
    return user


def create_or_get_user_by_id(db: Session, user_id: UUID, email: str | None = None) -> User:
    """Create a user with a specific UUID if not exists; update email if missing."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=user_id, email=email)
        db.add(user)
        db.flush()
    elif email and not user.email:
        user.email = email
        db.flush()
    return user


def ensure_user_exists(db: Session, email: str) -> User:
    """Ensure user exists in database (create if needed)."""
    return create_or_get_user(db, email)


def ensure_user_exists_by_id(db: Session, user_id: UUID, email: str | None = None) -> User:
    """Ensure user exists in database with a specific UUID."""
    return create_or_get_user_by_id(db, user_id, email=email)

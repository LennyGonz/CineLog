"""
Edit operations for User entity.
"""

from sqlalchemy.orm import Session
from app.models import User


def create_or_get_user(db: Session, email: str) -> User:
    """Create a user if not exists, otherwise return existing user."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email)
        db.add(user)
        db.flush()
    return user


def ensure_user_exists(db: Session, email: str) -> User:
    """Ensure user exists in database (create if needed)."""
    return create_or_get_user(db, email)

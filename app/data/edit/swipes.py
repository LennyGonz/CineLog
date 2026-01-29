"""
Edit operations for Swipe entity.
"""

from sqlalchemy.orm import Session
from app.models import Swipe
from uuid import UUID


def create_swipe(db: Session, user_id: UUID, movie_id: int, decision: int) -> Swipe:
    """Create a new swipe."""
    swipe = Swipe(user_id=user_id, movie_id=movie_id, decision=decision)
    db.add(swipe)
    return swipe

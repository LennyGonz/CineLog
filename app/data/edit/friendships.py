"""
Edit operations for Friendship entity.
"""

from sqlalchemy.orm import Session
from app.models import Friendship
from uuid import UUID


def create_or_update_friendship(
    db: Session, user_id: UUID, friend_id: UUID, status: str = "pending"
) -> Friendship:
    """Create or update a friendship."""
    friendship = (
        db.query(Friendship)
        .filter(Friendship.user_id == user_id, Friendship.friend_id == friend_id)
        .first()
    )

    if friendship:
        friendship.status = status
    else:
        friendship = Friendship(user_id=user_id, friend_id=friend_id, status=status)
        db.add(friendship)

    return friendship


def delete_friendship(db: Session, user_id: UUID, friend_id: UUID) -> int:
    """Delete friendship (bidirectional). Returns number of deleted rows."""
    from sqlalchemy import and_, or_

    deleted = (
        db.query(Friendship)
        .filter(
            or_(
                and_(Friendship.user_id == user_id, Friendship.friend_id == friend_id),
                and_(Friendship.user_id == friend_id, Friendship.friend_id == user_id),
            )
        )
        .delete()
    )

    return deleted

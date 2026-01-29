"""
Read operations for User entity.
"""

from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models import (
    User,
    Swipe,
    MasterListItem as MasterListModel,
    WatchLaterListItem,
    Friendship,
)
from uuid import UUID
from typing import Optional, List, Tuple


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email."""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: UUID) -> Optional[User]:
    """Get user by UUID."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_swiped_movie_ids(db: Session, user_id: UUID) -> set:
    """Get all movie IDs that a user has swiped on."""
    rows = db.query(Swipe.movie_id).filter(Swipe.user_id == user_id).all()
    return {r[0] for r in rows}


def get_user_master_list_movie_ids(db: Session, user_id: UUID) -> set:
    """Get all movie IDs in a user's master list."""
    rows = db.query(MasterListModel.movie_id).filter(MasterListModel.user_id == user_id).all()
    return {r[0] for r in rows}


def get_user_watch_later_movie_ids(db: Session, user_id: UUID) -> set:
    """Get all movie IDs in a user's watch later list."""
    rows = db.query(WatchLaterListItem.movie_id).filter(WatchLaterListItem.user_id == user_id).all()
    return {r[0] for r in rows}


def get_user_seen_movie_ids(db: Session, user_id: UUID) -> set:
    """Get all movie IDs that a user has seen (swipes, master list, or watch later)."""
    swiped = get_user_swiped_movie_ids(db, user_id)
    master = get_user_master_list_movie_ids(db, user_id)
    watch = get_user_watch_later_movie_ids(db, user_id)
    return swiped | master | watch


def get_user_swipes(db: Session, user_id: UUID) -> List[Tuple]:
    """Get all swipes for a user ordered by date descending."""
    return (
        db.query(Swipe.movie_id, Swipe.decision, Swipe.swiped_at)
        .filter(Swipe.user_id == user_id)
        .order_by(Swipe.swiped_at.desc())
        .all()
    )


def get_user_friends(db: Session, user_id: UUID) -> List[Tuple]:
    """Get all accepted friends for a user (bidirectional)."""
    # Outgoing friendships
    outgoing = (
        db.query(Friendship)
        .filter(Friendship.user_id == user_id, Friendship.status == "accepted")
        .all()
    )

    # Incoming friendships
    incoming = (
        db.query(Friendship)
        .filter(Friendship.friend_id == user_id, Friendship.status == "accepted")
        .all()
    )

    return outgoing, incoming


def get_friendship(db: Session, user_id: UUID, friend_id: UUID) -> Optional[Friendship]:
    """Get friendship relationship (bidirectional)."""
    return (
        db.query(Friendship)
        .filter(
            or_(
                (Friendship.user_id == user_id) & (Friendship.friend_id == friend_id),
                (Friendship.user_id == friend_id) & (Friendship.friend_id == user_id),
            ),
            Friendship.status == "accepted",
        )
        .first()
    )

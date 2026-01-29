"""
Read operations for list entities (master_list, watch_later_list).
"""

from sqlalchemy.orm import Session
from app.models import (
    MasterListItem as MasterListModel,
    WatchLaterListItem,
    Movie,
    MovieGenre,
)
from uuid import UUID
from typing import Optional, List


def get_master_list_item(db: Session, user_id: UUID, movie_id: int) -> Optional[MasterListModel]:
    """Get a specific master list item."""
    return (
        db.query(MasterListModel)
        .filter(MasterListModel.user_id == user_id, MasterListModel.movie_id == movie_id)
        .first()
    )


def get_watch_later_item(db: Session, user_id: UUID, movie_id: int) -> Optional[WatchLaterListItem]:
    """Get a specific watch later list item."""
    return (
        db.query(WatchLaterListItem)
        .filter(WatchLaterListItem.user_id == user_id, WatchLaterListItem.movie_id == movie_id)
        .first()
    )


def get_master_list_items(
    db: Session, user_id: UUID, genre_id: Optional[int] = None, sort_by: str = "date_added"
) -> List[tuple]:
    """Get all master list items for a user with optional genre filter."""
    query = (
        db.query(
            MasterListModel.movie_id,
            Movie.title,
            Movie.poster_path,
            Movie.overview,
            MasterListModel.rating,
            MasterListModel.notes,
            MasterListModel.added_at,
        )
        .join(Movie, MasterListModel.movie_id == Movie.id)
        .filter(MasterListModel.user_id == user_id)
    )

    if genre_id:
        query = (
            query.join(MovieGenre, Movie.id == MovieGenre.movie_id)
            .filter(MovieGenre.genre_id == genre_id)
            .distinct()
        )

    # Apply sorting
    if sort_by == "rating":
        query = query.order_by(MasterListModel.rating.desc().nullslast())
    else:  # date_added
        query = query.order_by(MasterListModel.added_at.desc())

    return query.all()


def get_watch_later_items(
    db: Session, user_id: UUID, genre_id: Optional[int] = None, sort_by: str = "priority"
) -> List[tuple]:
    """Get all watch later list items for a user with optional genre filter."""
    query = (
        db.query(
            WatchLaterListItem.movie_id,
            Movie.title,
            Movie.poster_path,
            Movie.overview,
            WatchLaterListItem.priority,
            WatchLaterListItem.added_at,
        )
        .join(Movie, WatchLaterListItem.movie_id == Movie.id)
        .filter(WatchLaterListItem.user_id == user_id)
    )

    if genre_id:
        query = (
            query.join(MovieGenre, Movie.id == MovieGenre.movie_id)
            .filter(MovieGenre.genre_id == genre_id)
            .distinct()
        )

    # Apply sorting
    if sort_by == "priority":
        query = query.order_by(
            WatchLaterListItem.priority.desc(), WatchLaterListItem.added_at.desc()
        )
    else:  # date_added
        query = query.order_by(WatchLaterListItem.added_at.desc())

    return query.all()


def get_friend_master_list_items(
    db: Session, friend_id: UUID, genre_id: Optional[int] = None
) -> List[tuple]:
    """Get a friend's master list items with optional genre filter."""
    query = (
        db.query(
            MasterListModel.movie_id,
            Movie.title,
            Movie.poster_path,
            MasterListModel.rating,
            MasterListModel.notes,
            MasterListModel.added_at,
        )
        .join(Movie, MasterListModel.movie_id == Movie.id)
        .filter(MasterListModel.user_id == friend_id)
    )

    if genre_id:
        query = (
            query.join(MovieGenre, Movie.id == MovieGenre.movie_id)
            .filter(MovieGenre.genre_id == genre_id)
            .distinct()
        )

    return query.order_by(MasterListModel.added_at.desc()).all()

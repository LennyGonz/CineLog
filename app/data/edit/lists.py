"""
Edit operations for list entities (master_list, watch_later_list).
"""

from sqlalchemy.orm import Session
from app.models import MasterListItem as MasterListModel, WatchLaterListItem
from uuid import UUID
from typing import Optional


def create_or_update_master_list_item(
    db: Session,
    user_id: UUID,
    movie_id: int,
    rating: Optional[float] = None,
    notes: Optional[str] = None,
) -> MasterListModel:
    """Create or update a master list item."""
    item = (
        db.query(MasterListModel)
        .filter(MasterListModel.user_id == user_id, MasterListModel.movie_id == movie_id)
        .first()
    )

    if item:
        if rating is not None:
            item.rating = rating
        if notes is not None:
            item.notes = notes
    else:
        item = MasterListModel(user_id=user_id, movie_id=movie_id, rating=rating, notes=notes)
        db.add(item)

    return item


def create_or_update_watch_later_item(
    db: Session, user_id: UUID, movie_id: int, priority: int = 1
) -> WatchLaterListItem:
    """Create or update a watch later list item."""
    item = (
        db.query(WatchLaterListItem)
        .filter(WatchLaterListItem.user_id == user_id, WatchLaterListItem.movie_id == movie_id)
        .first()
    )

    if item:
        item.priority = priority
    else:
        item = WatchLaterListItem(user_id=user_id, movie_id=movie_id, priority=priority)
        db.add(item)

    return item


def delete_master_list_item(db: Session, user_id: UUID, movie_id: int) -> int:
    """Delete a master list item. Returns number of deleted rows."""
    return (
        db.query(MasterListModel)
        .filter(MasterListModel.user_id == user_id, MasterListModel.movie_id == movie_id)
        .delete()
    )


def delete_watch_later_item(db: Session, user_id: UUID, movie_id: int) -> int:
    """Delete a watch later list item. Returns number of deleted rows."""
    return (
        db.query(WatchLaterListItem)
        .filter(WatchLaterListItem.user_id == user_id, WatchLaterListItem.movie_id == movie_id)
        .delete()
    )


def update_master_list_item(
    db: Session,
    user_id: UUID,
    movie_id: int,
    rating: Optional[float] = None,
    notes: Optional[str] = None,
) -> Optional[MasterListModel]:
    """Update an existing master list item."""
    item = (
        db.query(MasterListModel)
        .filter(MasterListModel.user_id == user_id, MasterListModel.movie_id == movie_id)
        .first()
    )

    if item:
        if rating is not None:
            item.rating = rating
        if notes is not None:
            item.notes = notes

    return item


def update_watch_later_item(
    db: Session, user_id: UUID, movie_id: int, priority: int
) -> Optional[WatchLaterListItem]:
    """Update an existing watch later list item."""
    item = (
        db.query(WatchLaterListItem)
        .filter(WatchLaterListItem.user_id == user_id, WatchLaterListItem.movie_id == movie_id)
        .first()
    )

    if item:
        item.priority = priority

    return item

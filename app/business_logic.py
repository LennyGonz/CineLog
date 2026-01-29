"""
Business logic layer - orchestrates data access operations and transforms data.
"""

from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional, Dict, Any

from external_services.tmdb import discover_movies, get_genres, get_movie_details
from .utils import decision_to_int, decode_cursor, encode_cursor
from .data import read, edit


# ========== SWIPE OPERATIONS ==========


def process_swipe(db: Session, user_id: str, movie_id: int, decision: str) -> Dict[str, Any]:
    """
    Process a swipe (like/nope) from a user.
    Returns response dict with ok status and details.
    """
    # Get or create user
    user = edit.ensure_user_exists(db, user_id)
    user_uuid = user.id

    # Ensure movie exists
    edit.ensure_movie_exists(db, movie_id)

    # Create swipe record
    decision_int = decision_to_int(decision)
    edit.create_swipe(db, user_uuid, movie_id, decision_int)

    db.commit()

    return {
        "ok": True,
        "user_id": user_id,
        "movie_id": movie_id,
        "decision": decision,
    }


def get_user_swipes_list(db: Session, user_id: str) -> List[Dict[str, Any]]:
    """
    Get all swipes for a user with formatted response.
    """
    user = read.get_user_by_email(db, user_id)

    if not user:
        return []

    swipes = read.get_user_swipes(db, user.id)

    def to_label(dec: int) -> str:
        return "like" if dec == 1 else "nope"

    return [
        {"movie_id": s[0], "decision": to_label(s[1]), "swiped_at": s[2].isoformat()}
        for s in swipes
    ]


# ========== DECK OPERATIONS ==========


def get_deck(
    db: Session, user_id: str, limit: int = 20, cursor: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get a deck of movies for swiping with cursor-based pagination.
    """
    # Decode cursor
    start_page, start_index = decode_cursor(cursor) if cursor else (1, 0)

    # Get user
    user = read.get_user_by_email(db, user_id)
    user_uuid = user.id if user else None

    # Get already seen movie IDs
    swiped_ids = set()
    if user_uuid:
        swiped_ids = read.get_user_seen_movie_ids(db, user_uuid)

    # Fetch from TMDB
    deck_cards = []
    current_page = start_page
    current_index = start_index
    next_cursor = None
    has_more = False

    while len(deck_cards) < limit and current_page <= 500:
        payload = discover_movies(page=current_page)
        results = payload.get("results", [])

        if not results:
            break

        # Skip to the start_index on first iteration
        if current_page == start_page:
            results = results[current_index:]

        # Filter out swiped movies
        for idx, m in enumerate(results):
            if m["id"] not in swiped_ids:
                deck_cards.append(
                    {
                        "id": m["id"],
                        "title": m.get("title") or m.get("name") or "Untitled",
                        "poster_path": m.get("poster_path"),
                        "backdrop_path": m.get("backdrop_path"),
                        "overview": m.get("overview"),
                        "release_date": m.get("release_date"),
                    }
                )

                if len(deck_cards) >= limit:
                    next_cursor = encode_cursor(current_page, current_index + idx + 1)
                    has_more = True
                    break

        if len(deck_cards) < limit:
            current_page += 1
            current_index = 0

    # Save movies to database
    for movie in deck_cards:
        edit.create_or_update_movie(
            db,
            movie["id"],
            movie["title"],
            release_date=movie.get("release_date"),
            poster_path=movie.get("poster_path"),
            backdrop_path=movie.get("backdrop_path"),
            overview=movie.get("overview"),
        )

    db.commit()

    # Sync genres in separate transaction
    for movie in deck_cards:
        try:
            movie_details = get_movie_details(movie["id"])
            genre_ids = movie_details.get("genres", [])

            for genre in genre_ids:
                genre_id = genre.get("id")
                if genre_id:
                    edit.add_movie_genre(db, movie["id"], genre_id)

            db.commit()
        except Exception:
            db.rollback()
            pass

    return {
        "results": deck_cards,
        "cursor": next_cursor,
        "has_more": has_more,
    }


# ========== GENRE SYNC OPERATIONS ==========


def sync_genres_from_tmdb(db: Session) -> Dict[str, Any]:
    """
    Fetch genres from TMDB and sync to database.
    """
    genres = get_genres()
    count = edit.sync_genres(db, genres)

    return {"ok": True, "genres_synced": count}


# ========== MOVIE INTERACTION OPERATIONS ==========


def process_movie_interaction(
    db: Session,
    user_id: str,
    movie_id: int,
    have_you_seen: bool,
    did_you_like: Optional[bool] = None,
    want_to_see: Optional[bool] = None,
    rating: Optional[float] = None,
    notes: Optional[str] = None,
    priority: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Process movie interaction (seen/unseen, like/nope, want to see).
    """
    # Get or create user
    user = edit.ensure_user_exists(db, user_id)
    user_uuid = user.id

    # Ensure movie exists
    edit.ensure_movie_exists(db, movie_id)

    action = "skipped"
    details = {}

    if have_you_seen:
        if did_you_like:
            # Save to master list
            edit.create_or_update_master_list_item(
                db, user_uuid, movie_id, rating=rating, notes=notes
            )
            action = "saved_to_master_list"
            details = {"rating": rating, "notes": notes}
    else:
        if want_to_see:
            # Save to watch later list
            edit.create_or_update_watch_later_item(db, user_uuid, movie_id, priority=priority or 1)
            action = "saved_to_watch_later"
            details = {"priority": priority or 1}

    db.commit()

    return {
        "ok": True,
        "user_id": user_id,
        "movie_id": movie_id,
        "action": action,
        "details": details if action != "skipped" else None,
    }


# ========== FRIEND OPERATIONS ==========


def send_friend_request(db: Session, user_id: str, friend_email: str) -> Dict[str, Any]:
    """
    Send a friend request from one user to another.
    """
    # Get users
    user = read.get_user_by_email(db, user_id)
    if not user:
        raise ValueError("User not found")

    friend = read.get_user_by_email(db, friend_email)
    if not friend:
        raise ValueError("Friend not found")

    if user.id == friend.id:
        raise ValueError("Cannot friend yourself")

    # Create friendship
    edit.create_or_update_friendship(db, user.id, friend.id, status="pending")
    db.commit()

    return {
        "ok": True,
        "message": f"Friend request sent to {friend_email}",
    }


def get_user_friends_list(db: Session, user_id: str) -> List[Dict[str, Any]]:
    """
    Get list of accepted friends for a user.
    """
    user = read.get_user_by_email(db, user_id)
    if not user:
        return []

    outgoing, incoming = read.get_user_friends(db, user.id)

    result = []

    # Process outgoing friendships
    for f in outgoing:
        friend = read.get_user_by_id(db, f.friend_id)
        if friend:
            result.append(
                {
                    "id": str(f.friend_id),
                    "email": friend.email,
                    "status": "accepted",
                    "created_at": f.created_at.isoformat(),
                }
            )

    # Process incoming friendships
    for f in incoming:
        friend = read.get_user_by_id(db, f.user_id)
        if friend:
            result.append(
                {
                    "id": str(f.user_id),
                    "email": friend.email,
                    "status": "accepted",
                    "created_at": f.created_at.isoformat(),
                }
            )

    # Sort by created_at descending
    result.sort(key=lambda x: x["created_at"], reverse=True)

    return result


def remove_friend(db: Session, user_id: str, friend_id: UUID) -> Dict[str, Any]:
    """
    Remove a friend relationship (bidirectional).
    """
    user = read.get_user_by_email(db, user_id)
    if not user:
        raise ValueError("User not found")

    edit.delete_friendship(db, user.id, friend_id)
    db.commit()

    return {"ok": True, "message": "Friendship removed"}


# ========== MASTER LIST OPERATIONS ==========


def get_user_master_list(
    db: Session, user_id: str, genre_id: Optional[int] = None, sort_by: str = "date_added"
) -> List[Dict[str, Any]]:
    """
    Get user's master list with optional genre filter and sorting.
    """
    user = read.get_user_by_email(db, user_id)
    if not user:
        return []

    items = read.get_master_list_items(db, user.id, genre_id=genre_id, sort_by=sort_by)

    result = []
    for item in items:
        movie_id, title, poster_path, overview, rating, notes, added_at = item
        genres = read.get_genres_for_movie(db, movie_id)

        result.append(
            {
                "movie_id": movie_id,
                "title": title,
                "poster_path": poster_path,
                "overview": overview,
                "genres": genres,
                "rating": rating,
                "notes": notes,
                "added_at": added_at.isoformat(),
            }
        )

    return result


def update_master_list_item(
    db: Session,
    user_id: str,
    movie_id: int,
    rating: Optional[float] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Update a master list item (rating/notes).
    """
    user = read.get_user_by_email(db, user_id)
    if not user:
        raise ValueError("User not found")

    item = read.get_master_list_item(db, user.id, movie_id)
    if not item:
        raise ValueError("Movie not in master list")

    edit.update_master_list_item(db, user.id, movie_id, rating=rating, notes=notes)
    db.commit()

    return {"ok": True, "movie_id": movie_id, "rating": rating, "notes": notes}


def delete_from_master_list(db: Session, user_id: str, movie_id: int) -> Dict[str, Any]:
    """
    Remove a movie from master list.
    """
    user = read.get_user_by_email(db, user_id)
    if not user:
        raise ValueError("User not found")

    deleted = edit.delete_master_list_item(db, user.id, movie_id)
    db.commit()

    if deleted == 0:
        raise ValueError("Movie not in master list")

    return {"ok": True, "message": "Movie removed from master list"}


def get_friend_master_list(
    db: Session, user_id: str, friend_id: UUID, genre_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Get a friend's master list (only if friends).
    """
    user = read.get_user_by_email(db, user_id)
    if not user:
        raise ValueError("User not found")

    # Verify friendship
    friendship = read.get_friendship(db, user.id, friend_id)
    if not friendship:
        raise ValueError("Not friends or friendship not accepted")

    items = read.get_friend_master_list_items(db, friend_id, genre_id=genre_id)

    result = []
    for item in items:
        movie_id, title, poster_path, rating, notes, added_at = item
        genres = read.get_genres_for_movie(db, movie_id)

        result.append(
            {
                "movie_id": movie_id,
                "title": title,
                "poster_path": poster_path,
                "genres": genres,
                "rating": rating,
                "notes": notes,
                "added_at": added_at.isoformat(),
            }
        )

    return result


# ========== WATCH LATER LIST OPERATIONS ==========


def get_user_watch_later(
    db: Session, user_id: str, genre_id: Optional[int] = None, sort_by: str = "priority"
) -> List[Dict[str, Any]]:
    """
    Get user's watch later list with optional genre filter and sorting.
    """
    user = read.get_user_by_email(db, user_id)
    if not user:
        return []

    items = read.get_watch_later_items(db, user.id, genre_id=genre_id, sort_by=sort_by)

    result = []
    for item in items:
        movie_id, title, poster_path, overview, priority, added_at = item
        genres = read.get_genres_for_movie(db, movie_id)

        result.append(
            {
                "movie_id": movie_id,
                "title": title,
                "poster_path": poster_path,
                "overview": overview,
                "genres": genres,
                "priority": priority,
                "added_at": added_at.isoformat(),
            }
        )

    return result


def update_watch_later_item(
    db: Session, user_id: str, movie_id: int, priority: int
) -> Dict[str, Any]:
    """
    Update a watch later list item (priority).
    """
    user = read.get_user_by_email(db, user_id)
    if not user:
        raise ValueError("User not found")

    item = read.get_watch_later_item(db, user.id, movie_id)
    if not item:
        raise ValueError("Movie not in watch later list")

    edit.update_watch_later_item(db, user.id, movie_id, priority)
    db.commit()

    return {"ok": True, "movie_id": movie_id, "priority": priority}


def delete_from_watch_later(db: Session, user_id: str, movie_id: int) -> Dict[str, Any]:
    """
    Remove a movie from watch later list.
    """
    user = read.get_user_by_email(db, user_id)
    if not user:
        raise ValueError("User not found")

    deleted = edit.delete_watch_later_item(db, user.id, movie_id)
    db.commit()

    if deleted == 0:
        raise ValueError("Movie not in watch later list")

    return {"ok": True, "message": "Movie removed from watch later list"}

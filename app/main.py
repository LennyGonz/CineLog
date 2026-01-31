"""
FastAPI main application file.
Routes delegate to business logic layer which orchestrates data access.
"""

import os

from fastapi import FastAPI, Depends, HTTPException, Query
from dotenv import load_dotenv
from typing import Literal, Optional
from sqlalchemy.orm import Session
from uuid import UUID

from .db import get_db
from .auth import get_current_user, AuthUser
from .schemas import (
    SwipeRequest,
    MovieInteractionRequest,
    FriendRequest,
    FriendAcceptRequest,
    SignupRequest,
    SignupResponse,
)
from .business_logic import (
    process_swipe,
    get_user_swipes_list,
    get_deck,
    sync_genres_from_tmdb,
    process_movie_interaction,
    send_friend_request,
    accept_friend_request,
    get_friend_requests,
    get_user_friends_list,
    remove_friend,
    get_user_master_list,
    update_master_list_item,
    delete_from_master_list,
    get_friend_master_list,
    get_user_watch_later,
    update_watch_later_item,
    delete_from_watch_later,
)
from .data import edit

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

app = FastAPI(title="CineLog API")


# ========== HEALTH CHECKS ==========


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/health/db")
def health_db(db: Session = Depends(get_db)):
    """Database connectivity check."""
    from .models import User

    db.query(User).first()
    return {"status": "ok", "db": "connected"}


@app.get("/debug/env")
def debug_env(current_user: AuthUser = Depends(get_current_user)):
    """Debug endpoint - returns environment info."""
    return {
        "database_url": DATABASE_URL,
    }


@app.get("/me")
def me(current_user: AuthUser = Depends(get_current_user)):
    """Return the authenticated user's identity."""
    return {"id": current_user.id, "email": current_user.email}


# ========== GENRE SYNC ==========


@app.post("/sync/genres")
def sync_genres(db: Session = Depends(get_db), current_user: AuthUser = Depends(get_current_user)):
    """Fetch genres from TMDB and sync them to the database."""
    try:
        result = sync_genres_from_tmdb(db)
        return result
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/signup", response_model=SignupResponse)
def signup(
    req: SignupRequest,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """Ensure a user record exists for the authenticated Supabase user."""
    try:
        user = edit.create_or_get_user_by_id(db, UUID(current_user.id), email=current_user.email)
        db.commit()

        return {
            "ok": True,
            "id": str(user.id),
            "email": user.email,
            "created_at": user.created_at.isoformat(),
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# ========== DECK & SWIPING ==========


@app.get("/deck")
def deck(
    limit: int = 20,
    cursor: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """Get a deck of movies for swiping with cursor-based pagination."""
    return get_deck(db, current_user.id, limit, cursor)


@app.post("/swipe")
def swipe(
    req: SwipeRequest,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """Process a swipe (like/nope) from a user."""
    try:
        return process_swipe(db, current_user.id, req.movie_id, req.decision)
    except Exception as e:
        db.rollback()
        if "duplicate" in str(e).lower() or "already" in str(e).lower():
            raise HTTPException(status_code=409, detail="Already swiped")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/swipes")
def get_swipes(db: Session = Depends(get_db), current_user: AuthUser = Depends(get_current_user)):
    """Get all swipes for a user."""
    return get_user_swipes_list(db, current_user.id)


# ========== MOVIE INTERACTIONS ==========


@app.post("/movie-interaction")
def movie_interaction(
    req: MovieInteractionRequest,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """Handle movie interaction flow (seen/unseen, like/nope, want to see)."""
    try:
        return process_movie_interaction(
            db,
            current_user.id,
            req.movie_id,
            req.have_you_seen,
            req.did_you_like,
            req.want_to_see,
            req.rating,
            req.notes,
            req.priority,
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# ========== FRIENDS ==========


@app.post("/friends/add")
def add_friend(
    req: FriendRequest,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """Send a friend request."""
    try:
        return send_friend_request(db, current_user.id, req.friend_email)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/friends/accept")
def accept_friend(
    req: FriendAcceptRequest,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """Accept a pending friend request."""
    try:
        return accept_friend_request(db, current_user.id, UUID(req.friend_id))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/friends/requests")
def friend_requests(
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """Get incoming/outgoing pending friend requests."""
    return get_friend_requests(db, current_user.id)


@app.get("/friends")
def get_friends(db: Session = Depends(get_db), current_user: AuthUser = Depends(get_current_user)):
    """Get all friends of a user (accepted friendships only)."""
    return get_user_friends_list(db, current_user.id)


@app.post("/friends/{friend_id}/remove")
def remove_friend_endpoint(
    friend_id: str,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """Remove a friendship."""
    try:
        return remove_friend(db, current_user.id, UUID(friend_id))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# ========== MASTER LIST ==========


@app.get("/master-list")
def get_master_list_endpoint(
    genre_id: Optional[int] = None,
    sort_by: Literal["date_added", "rating"] = "date_added",
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """Get user's own master list."""
    return get_user_master_list(db, current_user.id, genre_id, sort_by)


@app.put("/master-list/{movie_id}")
def update_master_list_endpoint(
    movie_id: int,
    rating: Optional[float] = Query(None, ge=0, le=5),
    notes: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """Update rating and/or notes for a movie in the master list."""
    try:
        return update_master_list_item(db, current_user.id, movie_id, rating, notes)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/master-list/{movie_id}")
def delete_master_list_endpoint(
    movie_id: int,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """Remove a movie from the master list."""
    try:
        return delete_from_master_list(db, current_user.id, movie_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/friends/{friend_id}/master-list")
def get_friend_master_list_endpoint(
    friend_id: str,
    genre_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """Get a friend's master list (only if friends)."""
    try:
        return get_friend_master_list(db, current_user.id, UUID(friend_id), genre_id)
    except ValueError as e:
        raise HTTPException(
            status_code=404 if "not found" in str(e).lower() else 403, detail=str(e)
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ========== WATCH LATER LIST ==========


@app.get("/watch-later-list")
def get_watch_later_endpoint(
    genre_id: Optional[int] = None,
    sort_by: Literal["date_added", "priority"] = "priority",
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """Get user's watch later list."""
    return get_user_watch_later(db, current_user.id, genre_id, sort_by)


@app.put("/watch-later-list/{movie_id}")
def update_watch_later_endpoint(
    movie_id: int,
    priority: int = Query(1, ge=1, le=5),
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """Update priority for a movie in the watch later list."""
    try:
        return update_watch_later_item(db, current_user.id, movie_id, priority)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/watch-later-list/{movie_id}")
def delete_watch_later_endpoint(
    movie_id: int,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """Remove a movie from the watch later list."""
    try:
        return delete_from_watch_later(db, current_user.id, movie_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

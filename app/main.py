import os

from fastapi import FastAPI, Depends, HTTPException
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Dict, Literal, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

from .db import get_db

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

app = FastAPI(title="CineLog API")

# --- Temporary in-memory store for MVP wiring ---
# Keyed by (user_id, movie_id) -> decision + timestamp
SWIPES: Dict[Tuple[str, int], dict] = {}

class SwipeRequest(BaseModel):
    user_id: str = Field(default="demo", min_length=1)  # "demo" for MVP
    movie_id: int = Field(gt=0)
    decision: Literal["like", "nope"]

def _decision_to_int(decision: str) -> int:
    return 1 if decision == "like" else -1


class SwipeResponse(BaseModel):
    ok: bool
    user_id: str
    movie_id: int
    decision: Literal["like", "nope"]
    swiped_at: str

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/db")
def health_db(db: Session = Depends(get_db)):
    # Simple query to verify DB connectivity
    db.execute(text("SELECT 1"))
    return {"status": "ok", "db": "connected"}


@app.get("/debug/env")
def debug_env():
    return {
        "database_url": DATABASE_URL,
    }


@app.get("/deck")
def deck(user_id: str = "demo", limit: int = 20, db: Session = Depends(get_db)):
    # 1) Find user UUID (users.email == user_id for MVP)
    user = db.execute(
        text("SELECT id FROM users WHERE email = :email"),
        {"email": user_id},
    ).fetchone()

    user_uuid = user[0] if user else None

    # 2) Get swiped movie ids
    swiped_ids = set()
    if user_uuid:
        rows = db.execute(
            text("SELECT movie_id FROM swipes WHERE user_id = :uid"),
            {"uid": user_uuid},
        ).fetchall()
        swiped_ids = {r[0] for r in rows}

    # 3) Deck source (MVP hardcoded list)
    source: List[dict] = [
        {"id": 550, "title": "Fight Club", "poster_path": "/bptfVGEQuv6vDTIMVCHjJ9Dz8PX.jpg"},
        {"id": 680, "title": "Pulp Fiction", "poster_path": "/d5iIlFn5s0ImszYzBPb8JPIfbXD.jpg"},
        {"id": 13, "title": "Forrest Gump", "poster_path": "/arw2vcBveWOVZr6pxd9XTd1TdQa.jpg"},
        {"id": 603, "title": "The Matrix", "poster_path": "/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg"},
        {"id": 155, "title": "The Dark Knight", "poster_path": "/qJ2tW6WMUDux911r6m7haRef0WH.jpg"},
    ]

    # 4) Filter out swiped movies
    remaining = [m for m in source if m["id"] not in swiped_ids]

    # 5) Upsert visible movies into DB (tiny cache builder)
    for movie in remaining[:limit]:
        db.execute(
            text("""
                INSERT INTO movies (id, title, poster_path, updated_at)
                VALUES (:id, :title, :poster_path, now())
                ON CONFLICT (id)
                DO UPDATE SET
                    title = EXCLUDED.title,
                    poster_path = EXCLUDED.poster_path,
                    updated_at = now()
            """),
            {
                "id": movie["id"],
                "title": movie["title"],
                "poster_path": movie.get("poster_path"),
            },
        )

    db.commit()

    # 6) Return deck
    return remaining[:limit]

@app.post("/swipe")
def swipe(req: SwipeRequest, db: Session = Depends(get_db)):
    # 1) Ensure a user row exists (demo user or future auth user)
    # For MVP, treat user_id="demo" as a stable pseudo-user.
    # We'll store it in users.email for now.
    user_row = db.execute(
        text("""
            INSERT INTO users (email)
            VALUES (:email)
            ON CONFLICT (email) DO UPDATE SET email = EXCLUDED.email
            RETURNING id
        """),
        {"email": req.user_id},
    ).fetchone()
    user_uuid = user_row[0]

    # 2) Ensure the movie exists in our movies cache.
    # For now, we store a placeholder title if we don't have details yet.
    db.execute(
        text("""
            INSERT INTO movies (id, title, updated_at)
            VALUES (:movie_id, :title, now())
            ON CONFLICT (id) DO UPDATE SET updated_at = now()
        """),
        {"movie_id": req.movie_id, "title": f"TMDB:{req.movie_id}"},
    )

    # 3) Insert swipe (block duplicates via PK(user_id, movie_id))
    decision_int = _decision_to_int(req.decision)

    try:
        db.execute(
            text("""
                INSERT INTO swipes (user_id, movie_id, decision)
                VALUES (:user_id, :movie_id, :decision)
            """),
            {"user_id": user_uuid, "movie_id": req.movie_id, "decision": decision_int},
        )
        db.commit()
    except Exception:
        db.rollback()
        # Most likely duplicate swipe due to PK constraint
        raise HTTPException(status_code=409, detail="Already swiped")

    return {
        "ok": True,
        "user_id": req.user_id,
        "movie_id": req.movie_id,
        "decision": req.decision,
    }

@app.get("/swipes")
def get_swipes(user_id: str = "demo", db: Session = Depends(get_db)):
    user = db.execute(
        text("SELECT id FROM users WHERE email = :email"),
        {"email": user_id},
    ).fetchone()

    if not user:
        return []

    user_uuid = user[0]
    rows = db.execute(
        text("""
            SELECT movie_id, decision, swiped_at
            FROM swipes
            WHERE user_id = :user_id
            ORDER BY swiped_at DESC
        """),
        {"user_id": user_uuid},
    ).fetchall()

    def to_label(dec: int) -> str:
        return "like" if dec == 1 else "nope"

    return [
        {"movie_id": r[0], "decision": to_label(r[1]), "swiped_at": r[2].isoformat()}
        for r in rows
    ]

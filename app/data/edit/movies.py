"""
Edit operations for Movie entity.
"""

from sqlalchemy.orm import Session
from app.models import Movie, Genre, MovieGenre
from typing import List


def create_or_update_movie(db: Session, movie_id: int, title: str, **kwargs) -> Movie:
    """Create or update a movie."""
    movie = db.query(Movie).filter(Movie.id == movie_id).first()

    if movie:
        movie.title = title
        for key, value in kwargs.items():
            if hasattr(movie, key) and value is not None:
                setattr(movie, key, value)
    else:
        movie = Movie(id=movie_id, title=title, **kwargs)
        db.add(movie)

    return movie


def ensure_movie_exists(db: Session, movie_id: int, title: str = None) -> Movie:
    """Ensure movie exists in database (create placeholder if needed)."""
    movie = db.query(Movie).filter(Movie.id == movie_id).first()

    if not movie:
        movie = Movie(id=movie_id, title=title or f"TMDB:{movie_id}")
        db.add(movie)
        db.flush()

    return movie


def sync_genre(db: Session, genre_id: int, name: str) -> Genre:
    """Create or update a genre."""
    genre = db.query(Genre).filter(Genre.id == genre_id).first()

    if genre:
        genre.name = name
    else:
        genre = Genre(id=genre_id, name=name)
        db.add(genre)

    return genre


def sync_genres(db: Session, genres: List[dict]) -> int:
    """Sync multiple genres. Returns count of synced genres."""
    count = 0
    for genre in genres:
        sync_genre(db, genre["id"], genre["name"])
        count += 1

    db.commit()
    return count


def add_movie_genre(db: Session, movie_id: int, genre_id: int) -> bool:
    """Add genre to movie if not already exists. Returns True if added."""
    existing = (
        db.query(MovieGenre)
        .filter(MovieGenre.movie_id == movie_id, MovieGenre.genre_id == genre_id)
        .first()
    )

    if not existing:
        db.add(MovieGenre(movie_id=movie_id, genre_id=genre_id))
        return True

    return False

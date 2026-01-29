"""
Read operations for Movie entity.
"""

from sqlalchemy.orm import Session
from app.models import Movie, Genre, MovieGenre
from typing import Optional, List


def get_movie_by_id(db: Session, movie_id: int) -> Optional[Movie]:
    """Get movie by TMDB ID."""
    return db.query(Movie).filter(Movie.id == movie_id).first()


def get_movie_with_genres(db: Session, movie_id: int) -> tuple:
    """Get movie with its genres."""
    movie = get_movie_by_id(db, movie_id)
    if not movie:
        return None, []

    genres = (
        db.query(Genre)
        .join(MovieGenre, Genre.id == MovieGenre.genre_id)
        .filter(MovieGenre.movie_id == movie_id)
        .all()
    )

    return movie, genres


def get_genres_for_movie(db: Session, movie_id: int) -> List[dict]:
    """Get list of genres for a movie."""
    genres = (
        db.query(Genre)
        .join(MovieGenre, Genre.id == MovieGenre.genre_id)
        .filter(MovieGenre.movie_id == movie_id)
        .all()
    )

    return [{"id": g.id, "name": g.name} for g in genres]

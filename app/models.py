"""
SQLAlchemy ORM models for CineLog database.
"""

from sqlalchemy import (
    Column,
    String,
    Text,
    Date,
    ForeignKey,
    Numeric,
    SmallInteger,
    BigInteger,
    TIMESTAMP,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)


class Genre(Base):
    __tablename__ = "genres"

    id = Column(BigInteger, primary_key=True)
    name = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)


class Movie(Base):
    __tablename__ = "movies"

    id = Column(BigInteger, primary_key=True)
    title = Column(String, nullable=False)
    release_date = Column(Date)
    poster_path = Column(String)
    backdrop_path = Column(String)
    overview = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class MovieGenre(Base):
    __tablename__ = "movie_genres"

    movie_id = Column(BigInteger, ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True)
    genre_id = Column(BigInteger, ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True)


class Swipe(Base):
    __tablename__ = "swipes"

    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    movie_id = Column(BigInteger, ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True)
    decision = Column(SmallInteger, nullable=False)
    swiped_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)


class MasterListItem(Base):
    __tablename__ = "master_list"

    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    movie_id = Column(BigInteger, ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True)
    rating = Column(Numeric(2, 1))
    notes = Column(Text)
    added_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)


class WatchLaterListItem(Base):
    __tablename__ = "watch_later_list"

    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    movie_id = Column(BigInteger, ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True)
    priority = Column(SmallInteger, default=1)
    added_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)


class Friendship(Base):
    __tablename__ = "friendships"

    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    friend_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    status = Column(String, default="pending")
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)

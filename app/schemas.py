"""
Pydantic models for API request/response schemas.
"""

from pydantic import BaseModel, Field
from typing import Literal, List, Optional


class SwipeRequest(BaseModel):
    user_id: str = Field(default="demo", min_length=1)
    movie_id: int = Field(gt=0)
    decision: Literal["like", "nope"]


class SwipeResponse(BaseModel):
    ok: bool
    user_id: str
    movie_id: int
    decision: Literal["like", "nope"]
    swiped_at: str


class MovieInteractionRequest(BaseModel):
    user_id: str = Field(default="demo", min_length=1)
    movie_id: int = Field(gt=0)
    have_you_seen: bool
    did_you_like: Optional[bool] = None
    want_to_see: Optional[bool] = None
    rating: Optional[float] = Field(None, ge=0, le=5)
    notes: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=5)


class MovieInteractionResponse(BaseModel):
    ok: bool
    user_id: str
    movie_id: int
    action: Literal["saved_to_master_list", "saved_to_watch_later", "skipped"]
    details: Optional[dict] = None


class FriendRequest(BaseModel):
    user_id: str = Field(default="demo", min_length=1)
    friend_email: str = Field(min_length=1)


class FriendResponse(BaseModel):
    id: str
    email: str
    status: Literal["pending", "accepted", "blocked"]
    created_at: str


class MasterListItem(BaseModel):
    movie_id: int
    title: str
    poster_path: Optional[str] = None
    genres: List[dict] = []
    rating: Optional[float] = None
    notes: Optional[str] = None
    added_at: str


class WatchLaterItem(BaseModel):
    movie_id: int
    title: str
    poster_path: Optional[str] = None
    genres: List[dict] = []
    priority: int
    added_at: str

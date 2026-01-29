"""
Read operations exports.
"""

from .users import (
    get_user_by_email,
    get_user_by_id,
    get_user_swiped_movie_ids,
    get_user_master_list_movie_ids,
    get_user_watch_later_movie_ids,
    get_user_seen_movie_ids,
    get_user_swipes,
    get_user_friends,
    get_friendship,
)

from .movies import (
    get_movie_by_id,
    get_movie_with_genres,
    get_genres_for_movie,
)

from .lists import (
    get_master_list_item,
    get_watch_later_item,
    get_master_list_items,
    get_watch_later_items,
    get_friend_master_list_items,
)

__all__ = [
    # Users
    "get_user_by_email",
    "get_user_by_id",
    "get_user_swiped_movie_ids",
    "get_user_master_list_movie_ids",
    "get_user_watch_later_movie_ids",
    "get_user_seen_movie_ids",
    "get_user_swipes",
    "get_user_friends",
    "get_friendship",
    # Movies
    "get_movie_by_id",
    "get_movie_with_genres",
    "get_genres_for_movie",
    # Lists
    "get_master_list_item",
    "get_watch_later_item",
    "get_master_list_items",
    "get_watch_later_items",
    "get_friend_master_list_items",
]

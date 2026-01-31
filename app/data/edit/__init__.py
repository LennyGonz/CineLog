"""
Edit operations exports.
"""

from .users import (
    create_or_get_user,
    create_or_get_user_by_id,
    ensure_user_exists,
    ensure_user_exists_by_id,
)

from .movies import (
    create_or_update_movie,
    ensure_movie_exists,
    sync_genre,
    sync_genres,
    add_movie_genre,
)

from .swipes import (
    create_swipe,
)

from .lists import (
    create_or_update_master_list_item,
    create_or_update_watch_later_item,
    delete_master_list_item,
    delete_watch_later_item,
    update_master_list_item,
    update_watch_later_item,
)

from .friendships import (
    create_or_update_friendship,
    delete_friendship,
)

__all__ = [
    # Users
    "create_or_get_user",
    "create_or_get_user_by_id",
    "ensure_user_exists",
    "ensure_user_exists_by_id",
    # Movies
    "create_or_update_movie",
    "ensure_movie_exists",
    "sync_genre",
    "sync_genres",
    "add_movie_genre",
    # Swipes
    "create_swipe",
    # Lists
    "create_or_update_master_list_item",
    "create_or_update_watch_later_item",
    "delete_master_list_item",
    "delete_watch_later_item",
    "update_master_list_item",
    "update_watch_later_item",
    # Friendships
    "create_or_update_friendship",
    "delete_friendship",
]

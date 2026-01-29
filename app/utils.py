"""
Utility functions for the CineLog API.
"""

import base64
import json
from typing import Tuple


def decision_to_int(decision: str) -> int:
    """Convert decision string to integer for database storage."""
    return 1 if decision == "like" else -1


def decode_cursor(cursor: str) -> Tuple[int, int]:
    """
    Decode pagination cursor.

    Returns:
        Tuple of (page, index) for resume position
    """
    try:
        decoded = base64.urlsafe_b64decode(cursor).decode("utf-8")
        cursor_data = json.loads(decoded)
        page = cursor_data.get("page", 1)
        index = cursor_data.get("index", 0)
        return page, index
    except Exception:
        return 1, 0


def encode_cursor(page: int, index: int) -> str:
    """
    Encode pagination cursor.

    Args:
        page: TMDB page number
        index: Index within the page results

    Returns:
        Base64-encoded cursor string
    """
    cursor_data = {"page": page, "index": index}
    return base64.urlsafe_b64encode(json.dumps(cursor_data).encode("utf-8")).decode("utf-8")

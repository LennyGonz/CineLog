import os
from dotenv import load_dotenv
import httpx

load_dotenv()

TMDB_BASE_URL = os.getenv("TMDB_BASE_URL", "https://api.themoviedb.org/3")
TMDB_LANGUAGE = os.getenv("TMDB_LANGUAGE", "en-US")
TMDB_READ_ACCESS_TOKEN = os.getenv("TMDB_READ_ACCESS_TOKEN")

if not TMDB_READ_ACCESS_TOKEN:
    raise RuntimeError("TMDB_READ_ACCESS_TOKEN is not set in .env")


def tmdb_headers() -> dict:
    return {
        "accept": "application/json",
        "Authorization": f"Bearer {TMDB_READ_ACCESS_TOKEN}",
    }


def tmdb_params(extra: dict | None = None) -> dict:
    params = {"language": TMDB_LANGUAGE}
    if extra:
        params.update(extra)
    return params


def discover_movies(page: int = 1) -> dict:
    url = f"{TMDB_BASE_URL}/discover/movie"
    with httpx.Client(timeout=10.0, headers=tmdb_headers()) as client:
        r = client.get(
            url,
            params=tmdb_params(
                {
                    "page": page,
                    "sort_by": "popularity.desc",
                    "include_adult": False,
                    "include_video": False,
                }
            ),
        )
        r.raise_for_status()
        return r.json()


def trending_movies(time_window: str = "day", page: int = 1) -> dict:
    url = f"{TMDB_BASE_URL}/trending/movie/{time_window}"
    with httpx.Client(timeout=10.0, headers=tmdb_headers()) as client:
        r = client.get(
            url,
            params=tmdb_params({"page": page}),
        )
        r.raise_for_status()
        return r.json()


def get_genres() -> dict:
    """Fetch all movie genres from TMDB and return as {id: name} dict."""
    url = f"{TMDB_BASE_URL}/genre/movie/list"
    with httpx.Client(timeout=10.0, headers=tmdb_headers()) as client:
        r = client.get(
            url,
            params=tmdb_params(),
        )
        r.raise_for_status()
        payload = r.json()
        # Return as list of {id, name} dicts
        return payload.get("genres", [])


def get_movie_details(movie_id: int) -> dict:
    """Fetch detailed info for a specific movie including genres."""
    url = f"{TMDB_BASE_URL}/movie/{movie_id}"
    with httpx.Client(timeout=10.0, headers=tmdb_headers()) as client:
        r = client.get(
            url,
            params=tmdb_params(),
        )
        r.raise_for_status()
        return r.json()

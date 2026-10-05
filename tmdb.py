"""Lấy poster phim từ TMDB (cần TMDB_API_KEY trong file .env)."""
import json
import os
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from config import ENV_PATH, POSTER_TIMEOUT, TMDB_IMAGE_BASE, TMDB_SEARCH_URL
from utils import fix_article, remove_release_year


def _read_env_file(path) -> dict:
    """Đọc file .env dạng KEY=VALUE, trả về dict. Không có file thì trả về {}."""
    values = {}
    try:
        with open(path, encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                values[key.strip()] = value.strip().strip('"').strip("'")
    except OSError:
        pass
    return values


def _get_api_key() -> Optional[str]:
    """Ưu tiên biến môi trường của hệ thống, không có thì đọc từ file .env."""
    return os.getenv("TMDB_API_KEY") or _read_env_file(ENV_PATH).get("TMDB_API_KEY")


def _search_poster_path(query: str, year: Optional[int], api_key: str) -> Optional[str]:
    params = {
        "api_key": api_key,
        "query": query,
        "language": "en-US",
        "include_adult": "false",
    }
    if year:
        params["year"] = year

    try:
        with urlopen(f"{TMDB_SEARCH_URL}?{urlencode(params)}", timeout=POSTER_TIMEOUT) as response:
            data = json.load(response)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return None

    for result in data.get("results", []):
        if result.get("poster_path"):
            return result["poster_path"]
    return None


def get_movie_poster(
    movie_title: str, year: Optional[int] = None, api_key: Optional[str] = None
) -> Optional[str]:
    """Trả về URL poster, hoặc None nếu không có / lỗi mạng / thiếu API key."""
    api_key = api_key or _get_api_key()
    query = fix_article(remove_release_year(movie_title))
    if not api_key or not query:
        return None

    # Thử có năm trước (chính xác hơn, tránh nhầm bản làm lại); không ra thì thử không năm.
    poster_path = _search_poster_path(query, year, api_key)
    if poster_path is None and year:
        poster_path = _search_poster_path(query, None, api_key)

    return f"{TMDB_IMAGE_BASE}{poster_path}" if poster_path else None
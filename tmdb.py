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


def _search_movie(query: str, year: Optional[int], api_key: str) -> Optional[dict]:
    """Tìm phim trên TMDB, trả về kết quả đầu tiên có poster (không có thì lấy kết quả đầu tiên)."""
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

    results = data.get("results", [])
    for result in results:
        if result.get("poster_path"):
            return result
    return results[0] if results else None

def _find_movie(movie_title: str, year: Optional[int], api_key: Optional[str]):
    """Trả về (movie, poster_path).

    movie       : kết quả khớp tên + năm nhất (dùng để lấy tóm tắt), hoặc None.
    poster_path : poster của movie; nếu movie không có poster thì thử tìm lại không năm.
    """
    query = fix_article(remove_release_year(movie_title))
    if not api_key or not query:
        return None, None

    movie = _search_movie(query, year, api_key)
    poster_path = movie.get("poster_path") if movie else None

    if year and not poster_path:
        retry = _search_movie(query, None, api_key)
        if retry:
            poster_path = retry.get("poster_path")
            if movie is None:
                movie = retry
    return movie, poster_path


def get_movie_poster(
    movie_title: str, year: Optional[int] = None, api_key: Optional[str] = None
) -> Optional[str]:
    """Trả về URL poster, hoặc None nếu không có / lỗi mạng / thiếu API key."""
    _, poster_path = _find_movie(movie_title, year, api_key or _get_api_key())
    return f"{TMDB_IMAGE_BASE}{poster_path}" if poster_path else None


def get_movie_details(
    movie_title: str, year: Optional[int] = None, api_key: Optional[str] = None
) -> Optional[dict]:
    """Trả về poster, tóm tắt (tiếng Anh), tên và ngày phát hành; None nếu không lấy được."""
    movie, poster_path = _find_movie(movie_title, year, api_key or _get_api_key())
    if not movie:
        return None
    return {
        "poster_url": f"{TMDB_IMAGE_BASE}{poster_path}" if poster_path else None,
        "overview": (movie.get("overview") or "").strip(),
        "tmdb_title": movie.get("title"),
        "release_date": movie.get("release_date"),
    }
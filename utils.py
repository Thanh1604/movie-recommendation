"""Các hàm nhỏ xử lý tên phim, dùng chung cho recommender và tmdb."""
import re
from typing import Optional

_YEAR_AT_END = re.compile(r"\s*\((\d{4})\)\s*$")
_ARTICLE_AT_END = re.compile(r"^(.*),\s*(The|A|An)$")


def remove_release_year(movie_title) -> str:
    """'Toy Story (1995)' -> 'Toy Story'."""
    return _YEAR_AT_END.sub("", str(movie_title)).strip()


def extract_release_year(movie_title) -> Optional[int]:
    """'Toy Story (1995)' -> 1995; không có năm thì trả về None."""
    match = _YEAR_AT_END.search(str(movie_title))
    return int(match.group(1)) if match else None


def fix_article(title: str) -> str:
    """MovieLens ghi 'Godfather, The' -> đổi thành 'The Godfather' để TMDB tìm đúng."""
    match = _ARTICLE_AT_END.match(title)
    return f"{match.group(2)} {match.group(1)}" if match else title
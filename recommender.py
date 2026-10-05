"""Mô hình gợi ý phim lai (Hybrid) đơn giản.

Điểm gợi ý của mỗi phim = WEIGHT_GENRE  x (độ giống nhau về thể loại)
                        + WEIGHT_RATING x (điểm đánh giá của đám đông)

- Phần 1 (Content-based): cosine similarity trên 19 cột thể loại.
- Phần 2 (Collaborative đơn giản): điểm trung bình phim do mọi người dùng chấm,
  có "làm dịu" (damping) để phim ít lượt chấm không bị đánh giá quá cao/thấp.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from config import DAMPING, GENRE_COLUMNS, TOP_N, WEIGHT_GENRE, WEIGHT_RATING
from utils import extract_release_year, remove_release_year


class MovieNotFoundError(Exception):
    """Không tìm thấy phim trong dữ liệu."""


@dataclass
class Recommendation:
    """Một phim được gợi ý, kèm thông tin để giải thích vì sao."""
    movie_id: int
    title: str                       # tên đã bỏ năm
    year: Optional[int]
    genre_similarity: float          # 0-100 (%), giống nhau về thể loại
    shared_genres: List[str] = field(default_factory=list)
    avg_rating: Optional[float] = None   # điểm trung bình thật; None nếu chưa ai chấm
    num_ratings: int = 0
    score: float = 0.0               # điểm tổng hợp dùng để xếp hạng


def compute_movie_stats(
    ratings: pd.DataFrame, damping: int = DAMPING
) -> Tuple[pd.DataFrame, float]:
    """Tính thống kê từng phim từ bảng ratings.

    Trả về (bảng thống kê index = MovieID, điểm trung bình toàn cục) với các cột:
      NumRatings   : số lượt chấm
      AvgRating    : điểm trung bình thật
      DampedRating : điểm trung bình đã làm dịu = (tổng điểm + damping * TB chung) / (số lượt + damping)
    """
    global_mean = float(ratings["Ratings"].mean())
    grouped = ratings.groupby("MovieID")["Ratings"].agg(total="sum", count="count")
    stats = pd.DataFrame({
        "NumRatings": grouped["count"],
        "AvgRating": grouped["total"] / grouped["count"],
        "DampedRating": (grouped["total"] + damping * global_mean)
                        / (grouped["count"] + damping),
    })
    return stats, global_mean


class HybridRecommender:
    def __init__(
        self,
        movies: pd.DataFrame,
        ratings: pd.DataFrame,
        weight_genre: float = WEIGHT_GENRE,
        weight_rating: float = WEIGHT_RATING,
    ):
        # reset_index để "vị trí hàng" khớp với "vị trí trong ma trận tương đồng"
        self.movies = movies.reset_index(drop=True)
        self.movies["MovieTitle"] = self.movies["MovieTitle"].fillna("")
        self.weight_genre = weight_genre
        self.weight_rating = weight_rating

        # 1. Content-based: ma trận độ giống nhau giữa mọi cặp phim
        self.genre_matrix = self.movies[GENRE_COLUMNS].values
        self.content_sim = cosine_similarity(self.genre_matrix)

        # 2. Điểm đánh giá của đám đông (chỉ tính từ `ratings` được truyền vào,
        #    nên khi đánh giá mô hình ta truyền tập train để tránh rò rỉ dữ liệu)
        stats, global_mean = compute_movie_stats(ratings)
        info = self.movies[["MovieID"]].join(stats, on="MovieID")
        self.num_ratings = info["NumRatings"].fillna(0).astype(int).values
        self.avg_rating = info["AvgRating"].values            # NaN nếu chưa ai chấm
        damped = info["DampedRating"].fillna(global_mean).values
        self.rating_score = (damped - 1) / 4                   # đưa về thang 0-1

        # Tên hiển thị (bỏ năm) và năm phát hành
        self.display_titles = self.movies["MovieTitle"].map(remove_release_year).tolist()
        self.years = self.movies["MovieTitle"].map(extract_release_year).tolist()

    def find_movie_index(self, movie_title: str) -> int:
        """Tìm vị trí phim theo tên: khớp chính xác trước, khớp một phần sau."""
        key = movie_title.strip().lower()
        titles = self.movies["MovieTitle"].str.lower()

        exact = np.flatnonzero((titles == key).values)
        if exact.size:
            return int(exact[0])

        partial = np.flatnonzero(titles.str.contains(key, regex=False).values)
        if partial.size:
            return int(partial[0])

        raise MovieNotFoundError(movie_title)

    def recommend(self, movie_title: str, top_n: int = TOP_N) -> List[Recommendation]:
        idx = self.find_movie_index(movie_title)

        # Điểm tổng hợp cho TẤT CẢ phim (tính một lần, không dùng vòng lặp)
        scores = (
            self.weight_genre * self.content_sim[idx]
            + self.weight_rating * self.rating_score
        )
        scores[idx] = -np.inf   # loại chính phim đang chọn một cách tường minh

        # kind="stable": khi hòa điểm thì giữ thứ tự cũ -> kết quả ổn định giữa các lần chạy
        order = np.argsort(-scores, kind="stable")

        # Không gợi ý lại tên trùng với phim đã chọn (MovieLens có vài tên bị lặp)
        # và bỏ dòng "unknown" của MovieLens.
        seen = {self.display_titles[idx], "unknown"}
        results: List[Recommendation] = []
        for i in order:
            title = self.display_titles[i]
            if title in seen:
                continue
            seen.add(title)
            results.append(self._build_recommendation(idx, int(i), float(scores[i])))
            if len(results) == top_n:
                break
        return results

    def _build_recommendation(self, idx: int, i: int, score: float) -> Recommendation:
        shared = [
            genre
            for genre, a, b in zip(GENRE_COLUMNS, self.genre_matrix[idx], self.genre_matrix[i])
            if a and b
        ]
        avg = self.avg_rating[i]
        return Recommendation(
            movie_id=int(self.movies.at[i, "MovieID"]),
            title=self.display_titles[i],
            year=self.years[i],
            genre_similarity=round(float(self.content_sim[idx, i]) * 100, 1),
            shared_genres=shared,
            avg_rating=None if np.isnan(avg) else round(float(avg), 2),
            num_ratings=int(self.num_ratings[i]),
            score=round(score, 4),
        )
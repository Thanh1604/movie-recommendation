"""Mô hình gợi ý phim lai (Hybrid) gồm 3 thành phần.

Điểm gợi ý = W_CONTENT x (giống nhau về thể loại)
           + W_COLLAB  x (cùng được người dùng yêu thích: item-item CF)
           + W_POP     x (chất lượng chung: điểm TB đã làm dịu)

- Content-based : cosine similarity trên 19 cột thể loại, có trọng số IDF
                  (thể loại hiếm như FilmNoir quan trọng hơn thể loại phổ biến như Drama).
- Collaborative : item-item CF. Mỗi phim là một vector điểm của người dùng (đã trừ điểm
                  trung bình của từng người), phim có người xem giống nhau thì giống nhau.
                  Có "shrinkage" để cặp phim ít người chấm chung không bị nhiễu.
- Popularity    : điểm trung bình có damping, chuẩn hóa min-max về 0-1.

Mô hình chỉ học từ `ratings` được truyền vào, nên khi đánh giá hãy truyền tập TRAIN.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

import config
from config import DAMPING, GENRE_COLUMNS, TOP_N
from utils import extract_release_year, remove_release_year

# Trọng số: nếu config.py chưa khai báo thì dùng giá trị mặc định này.
WEIGHT_CONTENT = getattr(config, "WEIGHT_CONTENT", 0.4)
WEIGHT_COLLAB = getattr(config, "WEIGHT_COLLAB", 0.4)
WEIGHT_POPULARITY = getattr(config, "WEIGHT_POPULARITY", 0.2)
# Cặp phim có k người chấm chung thì độ tương đồng CF nhân với k / (k + COLLAB_SHRINKAGE)
COLLAB_SHRINKAGE = getattr(config, "COLLAB_SHRINKAGE", 10)


class MovieNotFoundError(Exception):
    """Không tìm thấy phim trong dữ liệu."""


@dataclass
class Recommendation:
    """Một phim được gợi ý, kèm thông tin để giải thích vì sao."""
    movie_id: int
    title: str                           # tên đã bỏ năm
    year: Optional[int]
    genre_similarity: float              # 0-100 (%), giống nhau về thể loại
    collab_similarity: float = 0.0       # 0-100 (%), cùng được người dùng yêu thích
    shared_genres: List[str] = field(default_factory=list)
    avg_rating: Optional[float] = None   # điểm trung bình thật; None nếu chưa ai chấm
    num_ratings: int = 0
    score: float = 0.0                   # điểm tổng hợp 0-1 dùng để xếp hạng
    compatibility: float = 0.0           # score x 100 (%), dùng để hiển thị "độ phù hợp"


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
        weight_content: float = WEIGHT_CONTENT,
        weight_collab: float = WEIGHT_COLLAB,
        weight_popularity: float = WEIGHT_POPULARITY,
    ):
        # reset_index để "vị trí hàng" khớp với "vị trí trong các ma trận tương đồng"
        self.movies = movies.reset_index(drop=True)
        self.movies["MovieTitle"] = self.movies["MovieTitle"].fillna("")

        # Chuẩn hóa để tổng 3 trọng số luôn bằng 1 (điểm tổng hợp nằm trong 0-1)
        total = weight_content + weight_collab + weight_popularity
        self.w_content = weight_content / total
        self.w_collab = weight_collab / total
        self.w_pop = weight_popularity / total

        # 1. Content-based (thể loại, có trọng số IDF)
        self.genre_matrix = self.movies[GENRE_COLUMNS].values
        self.content_sim = self._build_content_sim()

        # 2. Thống kê đánh giá + điểm phổ biến (0-1)
        stats, global_mean = compute_movie_stats(ratings)
        info = self.movies[["MovieID"]].join(stats, on="MovieID")
        self.num_ratings = info["NumRatings"].fillna(0).astype(int).values
        self.avg_rating = info["AvgRating"].values            # NaN nếu chưa ai chấm
        damped = info["DampedRating"].fillna(global_mean).values
        lo, hi = damped.min(), damped.max()
        # min-max theo dữ liệu thật để thành phần này thực sự trải đủ 0-1
        self.rating_score = (damped - lo) / (hi - lo) if hi > lo else np.zeros_like(damped)

        # 3. Collaborative item-item
        self.collab_sim = self._build_collab_sim(ratings)

        # Tên hiển thị (bỏ năm) và năm phát hành
        self.display_titles = self.movies["MovieTitle"].map(remove_release_year).tolist()
        self.years = [
            None if pd.isna(y) else int(y)
            for y in self.movies["MovieTitle"].map(extract_release_year)
        ]

    # ------------------------------------------------------------------
    # Xây dựng các ma trận tương đồng
    # ------------------------------------------------------------------
    def _build_content_sim(self) -> np.ndarray:
        genres = self.genre_matrix.astype(np.float32)
        doc_freq = genres.sum(axis=0)
        idf = np.log((len(genres) + 1) / (doc_freq + 1)) + 1     # thể loại càng hiếm, idf càng lớn
        return cosine_similarity(genres * idf)

    def _build_collab_sim(self, ratings: pd.DataFrame) -> np.ndarray:
        """Ma trận tương đồng phim-phim dựa trên hành vi chấm điểm của người dùng."""
        n_movies = len(self.movies)
        r = ratings[["UserID", "MovieID", "Ratings"]].copy()

        # Trừ điểm trung bình của từng người để bỏ khác biệt "người dễ tính / khó tính"
        r["Centered"] = r["Ratings"] - r.groupby("UserID")["Ratings"].transform("mean")

        movie_pos = pd.Series(np.arange(n_movies), index=self.movies["MovieID"].values)
        r = r[r["MovieID"].isin(movie_pos.index)]
        rows = movie_pos.loc[r["MovieID"].values].values
        cols = pd.factorize(r["UserID"])[0]
        n_users = cols.max() + 1 if len(cols) else 0
        if n_users == 0:
            return np.zeros((n_movies, n_movies), dtype=np.float32)

        centered = np.zeros((n_movies, n_users), dtype=np.float32)
        present = np.zeros((n_movies, n_users), dtype=np.float32)   # 1 nếu có chấm điểm
        centered[rows, cols] = r["Centered"].values
        present[rows, cols] = 1.0

        sim = np.clip(cosine_similarity(centered), 0.0, 1.0)   # chỉ giữ tương quan dương
        co_count = present @ present.T                          # số người chấm chung từng cặp phim
        shrink = co_count / (co_count + COLLAB_SHRINKAGE)       # ít người chấm chung -> giảm tin cậy
        return sim * shrink

    # ------------------------------------------------------------------
    # Tìm phim và gợi ý
    # ------------------------------------------------------------------
    def find_movie_index(self, movie_title: str) -> int:
        """Tìm vị trí phim theo tên: khớp chính xác trước, khớp một phần sau.

        Nếu có nhiều phim khớp thì chọn phim có nhiều lượt chấm nhất.
        """
        key = movie_title.strip().lower()
        if not key:
            raise MovieNotFoundError(movie_title)
        titles = self.movies["MovieTitle"].str.lower().str.strip()

        for mask in (titles == key, titles.str.contains(key, regex=False)):
            positions = np.flatnonzero(mask.values)
            if positions.size:
                return int(positions[np.argmax(self.num_ratings[positions])])

        raise MovieNotFoundError(movie_title)

    def recommend(self, movie_title: str, top_n: int = TOP_N) -> List[Recommendation]:
        idx = self.find_movie_index(movie_title)

        # Điểm tổng hợp cho TẤT CẢ phim (tính một lần, không dùng vòng lặp)
        scores = (
            self.w_content * self.content_sim[idx]
            + self.w_collab * self.collab_sim[idx]
            + self.w_pop * self.rating_score
        )
        scores[idx] = -np.inf   # loại chính phim đang chọn

        # kind="stable": khi hòa điểm thì giữ thứ tự cũ -> kết quả ổn định giữa các lần chạy
        order = np.argsort(-scores, kind="stable")

        # Loại trùng theo tên ĐẦY ĐỦ (có năm) để các bản làm lại như Hamlet 1990/1996
        # không bị coi là một; vẫn loại các dòng bị lặp trong MovieLens và dòng "unknown".
        full_titles = self.movies["MovieTitle"].str.lower().str.strip().tolist()
        seen = {full_titles[idx], "unknown"}
        results: List[Recommendation] = []
        for i in order:
            full = full_titles[i]
            if full in seen:
                continue
            seen.add(full)
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
            collab_similarity=round(float(self.collab_sim[idx, i]) * 100, 1),
            shared_genres=shared,
            avg_rating=None if np.isnan(avg) else round(float(avg), 2),
            num_ratings=int(self.num_ratings[i]),
            score=round(score, 4),
            compatibility=round(score * 100, 1),
        )
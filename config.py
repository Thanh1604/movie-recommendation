"""Cấu hình chung cho cả dự án.

Mọi con số / đường dẫn dùng ở nhiều nơi đều đặt ở đây để dễ tìm, dễ sửa
và dễ giải thích khi bảo vệ.
"""
from pathlib import Path

# ---------- Đường dẫn (không phụ thuộc thư mục đang chạy lệnh) ----------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RESULTS_DIR = BASE_DIR / "results"

MOVIES_PATH = DATA_DIR / "cleaned_movies.csv"
RATINGS_PATH = DATA_DIR / "cleaned_ratings.csv"
ENV_PATH = BASE_DIR / ".env"

# ---------- 19 cột thể loại của MovieLens ----------
GENRE_COLUMNS = [
    "Unknown", "Action", "Adventure", "Animation", "Children", "Comedy",
    "Crime", "Documentary", "Drama", "Fantasy", "FilmNoir", "Horror",
    "Musical", "Mystery", "Romance", "SciFi", "Thriller", "War", "Western",
]

# ---------- Tham số của mô hình gợi ý ----------
TOP_N = 5               # số phim gợi ý trả về
WEIGHT_GENRE = 0.7      # trọng số của "giống nhau về thể loại"
WEIGHT_RATING = 0.3     # trọng số của "điểm đánh giá của đám đông"
DAMPING = 20            # phim càng ít lượt chấm thì điểm càng bị kéo về mức trung bình chung

# ---------- Tham số giao diện / thống kê ----------
MIN_RATINGS_FOR_TOP = 50    # ngưỡng lượt chấm tối thiểu khi xếp "phim điểm cao nhất"

# ---------- TMDB (poster) ----------
POSTER_TIMEOUT = 10
TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

# ---------- Đánh giá mô hình ----------
TEST_SIZE = 0.2
RANDOM_STATE = 42
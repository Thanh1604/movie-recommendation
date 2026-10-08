import streamlit as st
import pandas as pd
from config import MOVIES_PATH, RATINGS_PATH
from recommender import HybridRecommender, MovieNotFoundError
from tmdb import get_movie_details, get_movie_poster
import streamlit.components.v1 as components
import html as html_lib
# CẤU HÌNH TRANG

st.set_page_config(
    page_title="Hệ Thống Đề Xuất Phim",
    layout="wide"
)

# CHẾ ĐỘ GIAO DIỆN

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

with st.sidebar:
    st.subheader("⚙️ Giao diện")

    st.toggle(
        "🌙 Chế độ tối",
        key="dark_mode"
    )

if st.session_state.dark_mode:
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #0E1117;
            color: white;
        }

        [data-testid="stSidebar"] {
            background-color: #161B22;
        }

        h1, h2, h3, h4, h5, h6, p, label {
            color: white !important;
        }

        .stTextInput input {
            background-color: #262730;
            color: white;
        }

        div[data-baseweb="select"] > div {
            background-color: #262730;
            color: white;
        }

        [data-testid="stDataFrame"] {
            background-color: #161B22;
        }

        /* NÚT */
        .stButton > button {
            background-color: #262730;
            color: white;
            border: 1px solid #555555;
        }

        .stButton > button:hover {
            background-color: #3A3F4B;
            color: white;
            border-color: #777777;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

else:
    st.markdown(
        """
        <style>
        .stApp {
            background-color: white;
            color: #222222;
        }

        [data-testid="stSidebar"] {
            background-color: #F5F5F5;
        }

        h1, h2, h3, h4, h5, h6, p, label {
            color: #222222 !important;
        }

        .stTextInput input {
            background-color: white;
            color: #222222;
        }

        div[data-baseweb="select"] > div {
            background-color: white;
            color: #222222;
        }

        /* NÚT */
        .stButton > button {
            background-color: white;
            color: #222222;
            border: 1px solid #CCCCCC;
        }

        .stButton > button:hover {
            background-color: #F0F0F0;
            color: #222222;
            border-color: #999999;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

st.title("Hệ Thống Phân Tích và Đề Xuất Phim")
st.write(
    "Ứng dụng phân tích dữ liệu phim và đề xuất "
    "các bộ phim tương tự."
)


# ĐỌC DỮ LIỆU

@st.cache_data
def load_data():
    movies = pd.read_csv(
        "data/cleaned_movies.csv"
    )

    ratings = pd.read_csv(
        "data/cleaned_ratings.csv"
    )

    return movies, ratings

@st.cache_data
def load_movie_poster(movie_title, year=None):
    return get_movie_poster(movie_title, year)

@st.cache_resource
def load_recommender():
    movies, ratings = load_data()
    return HybridRecommender(movies, ratings)

try:
    movies, ratings = load_data()

except Exception as e:
    st.error(
        "Không thể đọc dữ liệu. "
        "Hãy kiểm tra lại đường dẫn và tên file CSV."
    )
    st.stop()

# XỬ LÝ DỮ LIỆU CƠ BẢN

movies["MovieTitle"] = movies["MovieTitle"].fillna(
    "Không có tên phim"
)

ratings["Ratings"] = pd.to_numeric(
    ratings["Ratings"],
    errors="coerce"
)

movies["ReleaseDate"] = pd.to_datetime(
    movies["ReleaseDate"],
    errors="coerce"
)

ratings["Timestamp"] = pd.to_datetime(
    ratings["Timestamp"],
    errors="coerce"
)

# TOP 10 PHIM HOT

@st.cache_data
def load_top_movies(top_n=10):
    """Top phim hot kèm URL poster (cache để không gọi TMDB lại mỗi lần chạy)."""
    recommender = load_recommender()
    items = []
    for rec in recommender.top_movies(top_n):
        items.append({
            "title": rec.title,
            "avg_rating": rec.avg_rating,
            "poster_url": load_movie_poster(rec.title, rec.year),
        })
    return items


def build_carousel_html(items):
    cards = []
    for item in items:
        title = html_lib.escape(item["title"])
        rating = f"⭐ {item['avg_rating']}" if item["avg_rating"] is not None else ""
        if item["poster_url"]:
            cards.append(
                f'<div class="movie-card" title="{title}">'
                f'<img src="{item["poster_url"]}" alt="{title}">'
                f'<div class="badge">{rating}</div></div>'
            )
        else:
            cards.append(f'<div class="movie-card" title="{title}">{title}</div>')

    return """
<!DOCTYPE html>
<html>
<head>
<style>
body { margin: 0; padding: 0; background: transparent; font-family: Arial, sans-serif; }
.carousel { width: 960px; max-width: 100%; margin: 0 auto; overflow: hidden; }
.track { display: flex; gap: 15px; width: max-content; transform: translateX(0); }
.movie-card {
    position: relative;
    width: 180px; height: 250px; flex: 0 0 180px;
    border-radius: 10px; overflow: hidden;
    background: #eeeeee; border: 1px solid #cccccc;
    display: flex; align-items: center; justify-content: center;
    text-align: center; padding: 6px; box-sizing: border-box;
    font-size: 16px; font-weight: bold; color: #777;
}
.movie-card img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
.badge {
    position: absolute; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.65); color: #fff;
    font-size: 14px; padding: 4px 0; text-align: center;
}
</style>
</head>
<body>
<div class="carousel">
    <div class="track" id="movieTrack">
        """ + "\n".join(cards) + """
    </div>
</div>
<script>
const track = document.getElementById("movieTrack");
const step = 195;
const maxPosition = 5;
let position = 0;

function moveCarousel() {
    if (position === maxPosition) {
        setTimeout(function() {
            track.style.transition = "none";
            position = 0;
            track.style.transform = "translateX(0)";
            setTimeout(function() {
                track.style.transition = "transform 1.5s ease";
                moveCarousel();
            }, 1500);
        }, 1500);
        return;
    }
    position++;
    track.style.transition = "transform 1.5s ease";
    track.style.transform = "translateX(-" + (position * step) + "px)";
    setTimeout(moveCarousel, 3000);
}
moveCarousel();
</script>
</body>
</html>
"""


st.subheader("🔥 Top 10 Phim Hot")

top_items = load_top_movies(10)
if top_items:
    components.html(build_carousel_html(top_items), height=280, scrolling=False)
else:
    st.caption("Chưa có dữ liệu để hiển thị top phim.")

# TRẠNG THÁI VÀ HÀM CHO TRANG CHI TIẾT PHIM

for _key in ("recommendations", "selected_recommendation_movie", "detail_rec"):
    if _key not in st.session_state:
        st.session_state[_key] = None

# Giữ lại lựa chọn trong selectbox khi chuyển sang trang chi tiết rồi quay lại
if "selected_movie" in st.session_state:
    st.session_state.selected_movie = st.session_state.selected_movie


def open_detail(rec):
    st.session_state.detail_rec = rec


def close_detail():
    st.session_state.detail_rec = None


@st.cache_data
def load_movie_details(movie_title, year=None):
    return get_movie_details(movie_title, year)


@st.cache_data
def load_rating_distribution(movie_id):
    """Số lượt chấm của từng mức 1-5 sao: {1: n1, 2: n2, ...}."""
    counts = (
        ratings.loc[ratings["MovieID"] == movie_id, "Ratings"]
        .dropna()
        .astype(int)
        .value_counts()
    )
    return {star: int(counts.get(star, 0)) for star in range(1, 6)}


def show_movie_detail(rec):
    st.button("← Quay lại danh sách gợi ý", on_click=close_detail)

    details = load_movie_details(rec.title, rec.year)
    poster_url = details["poster_url"] if details else None
    overview = details["overview"] if details else ""

    col_poster, col_info = st.columns([1, 2])

    with col_poster:
        if poster_url:
            st.image(poster_url, width=300)
        else:
            st.caption("Không có poster")

    with col_info:
        st.header(rec.title)

        distribution = load_rating_distribution(rec.movie_id)
        total = sum(distribution.values())

        st.subheader("Điểm đánh giá của người dùng")
        if total == 0:
            st.caption("Phim này chưa có lượt đánh giá.")
        else:
            st.write(f"⭐ **{rec.avg_rating}** / 5  ·  {total} lượt chấm")
            for star in range(5, 0, -1):
                count = distribution[star]
                label_col, bar_col, number_col = st.columns([1, 6, 2])
                label_col.write(f"{star} ⭐")
                bar_col.progress(count / total)
                number_col.write(f"{count} ({count / total * 100:.0f}%)")

        st.subheader("Tóm tắt nội dung")
        if overview:
            st.write(overview)
        else:
            st.caption(
                "Chưa lấy được tóm tắt cho phim này "
                "(kiểm tra TMDB_API_KEY trong .env hoặc kết nối mạng)."
            )
# TẠO TABS

tab1, tab2 = st.tabs([
    "Gợi Ý Phim",
    "Phân Tích Dữ Liệu"
])

# TAB 1: GỢI Ý PHIM

with tab1:

    if st.session_state.detail_rec is not None:
        show_movie_detail(st.session_state.detail_rec)

    else:

        st.header("Tìm Phim Tương Tự")

        st.write(
            "Chọn một bộ phim bạn yêu thích. "
            "Hệ thống sẽ đề xuất các bộ phim tương tự."
        )

        # Danh sách phim
        movie_list = (
            movies["MovieTitle"]
            .dropna()
            .sort_values()
            .unique()
            .tolist()
        )

        selected_movie = st.selectbox(
            "Chọn bộ phim:",
            movie_list,
            key="selected_movie"
        )
        
        if st.button("Hiển Thị Gợi Ý"):
            try:
                recommender = load_recommender()
                st.session_state.recommendations = recommender.recommend(
                    selected_movie, top_n=5
                )
                st.session_state.selected_recommendation_movie = selected_movie
            except MovieNotFoundError:
                st.session_state.recommendations = None
                st.warning(f"Không tìm thấy phim: {selected_movie}")

        recommendations = st.session_state.recommendations

        if recommendations:
            st.success(
                f"Đề xuất cho phim: {st.session_state.selected_recommendation_movie}"
            )
            st.subheader("Các phim tương tự")

            result_columns = st.columns(len(recommendations))
            for index, rec in enumerate(recommendations, start=1):
                with result_columns[index - 1]:
                    st.write(f"{index}. {rec.title}")
                    st.caption(f"Độ phù hợp: {rec.compatibility:.1f}%")
                    if rec.avg_rating is not None:
                        st.caption(f"⭐ {rec.avg_rating}")
                    else:
                        st.caption("⭐ Chưa có đánh giá")

                    poster_url = load_movie_poster(rec.title, rec.year)
                    if poster_url:
                        st.image(poster_url, width=180)
                    else:
                        st.caption("Không có poster")
                    st.button(
                        "Xem chi tiết",
                        key=f"detail_{rec.movie_id}",
                        on_click=open_detail,
                        args=(rec,),
                    )

    

# TAB 2: PHÂN TÍCH DỮ LIỆU

with tab2:

    st.header("Phân Tích Dữ Liệu")

    st.write(
        "Khu vực này hiển thị thông tin tổng quan "
        "và kết quả phân tích dữ liệu phim."
    )

    # TỔNG QUAN

    st.subheader("Tổng Quan Dữ Liệu")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Số lượng phim",
            len(movies)
        )

    with col2:
        st.metric(
            "Số lượt đánh giá",
            len(ratings)
        )

    with col3:
        st.metric(
            "Số người dùng",
            ratings["UserID"].nunique()
        )

    # THỐNG KÊ ĐÁNH GIÁ

    st.subheader("Thống Kê Đánh Giá")

    rating_col1, rating_col2, rating_col3 = st.columns(3)

    with rating_col1:
        average_rating = ratings["Ratings"].mean()

        st.metric(
            "Điểm đánh giá trung bình",
            f"{average_rating:.2f}"
        )

    with rating_col2:
        highest_rating = ratings["Ratings"].max()

        st.metric(
            "Điểm đánh giá cao nhất",
            f"{highest_rating:.0f}"
        )

    with rating_col3:
        lowest_rating = ratings["Ratings"].min()

        st.metric(
            "Điểm đánh giá thấp nhất",
            f"{lowest_rating:.0f}"
        )

    # KHU VỰC EDA CỦA TV3

    st.subheader("Biểu Đồ Phân Tích")

    st.write(
        "Các biểu đồ dưới đây thể hiện kết quả "
        "phân tích dữ liệu phim và hành vi người dùng."
    )

    # 1. PHÂN TÍCH ĐÁNH GIÁ

    with st.expander(
        "📊 Phân tích đánh giá",
        expanded=True
    ):

        st.markdown("### Phân bố điểm đánh giá")

        st.image(
            "results/rating_distribution.png",
            width=600
        )

        st.markdown(
            "### Số lượt đánh giá theo thể loại"
        )

        st.image(
            "results/rating_count_by_genre.png",
            width=600
        )

        st.markdown(
            "### Điểm đánh giá trung bình theo thể loại"
        )

        st.image(
            "results/average_rating_by_genre.png",
            width=600
        )

    # 2. PHÂN TÍCH PHIM

    with st.expander("🎬 Phân tích phim"):

        st.markdown(
            "### Top 10 phim được đánh giá nhiều nhất"
        )

        st.image(
            "results/top_10_most_rated_movies.png",
            width=600
        )

        st.markdown(
            "### Phân bố số lượt đánh giá trên mỗi phim"
        )

        st.image(
            "results/movie_rating_count_distribution.png",
            width=600
        )

        st.markdown(
            "### Phân bố điểm trung bình của phim"
        )

        st.image(
            "results/movie_average_rating_distribution.png",
            width=600
        )

    # 3. PHÂN TÍCH NGƯỜI DÙNG

    with st.expander("👤 Phân tích người dùng"):

        st.markdown(
            "### Top 10 người dùng hoạt động nhiều nhất"
        )

        st.image(
            "results/top_10_active_users.png",
            width=600
        )

        st.markdown(
            "### Phân bố số lượt đánh giá của người dùng"
        )

        st.image(
            "results/user_activity_distribution.png",
            width=600
        )

        st.markdown(
            "### Phân bố điểm trung bình của người dùng"
        )

        st.image(
            "results/user_average_rating_distribution.png",
            width=600
        )

    # 4. PHÂN TÍCH THEO THỜI GIAN

    with st.expander("📅 Phân tích theo thời gian"):

        st.markdown(
            "### Số lượt đánh giá theo năm"
        )

        st.image(
            "results/ratings_by_year.png",
            width=600
        )

        st.markdown(
            "### Điểm đánh giá trung bình theo năm"
        )

        st.image(
            "results/average_rating_by_year.png",
            width=600
        )

    # 5. PHÂN TÍCH THỂ LOẠI

    with st.expander("🎭 Phân tích thể loại"):

        st.markdown(
            "### Số lượng phim theo thể loại"
        )

        st.image(
            "results/genre_distribution.png",
            width=600
        )
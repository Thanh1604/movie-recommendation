import streamlit as st
import pandas as pd
from config import MOVIES_PATH, RATINGS_PATH
from recommender import HybridRecommender, MovieNotFoundError
from tmdb import get_movie_poster

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

# TẠO TABS

tab1, tab2 = st.tabs([
    "Gợi Ý Phim",
    "Phân Tích Dữ Liệu"
])

# TAB 1: GỢI Ý PHIM

with tab1:

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
    if "recommendations" not in st.session_state:
        st.session_state.recommendations = None

    if "selected_recommendation_movie" not in st.session_state:
        st.session_state.selected_recommendation_movie = None

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
                title = rec.title + (f" ({rec.year})" if rec.year else "")
                st.write(f"{index}. {title}")
                st.caption(f"Giống thể loại: {rec.genre_similarity:.1f}%")
                if rec.avg_rating is not None:
                    st.caption(f"⭐ {rec.avg_rating} ({rec.num_ratings} lượt chấm)")

                poster_url = load_movie_poster(rec.title, rec.year)
                if poster_url:
                    st.image(poster_url, width=180)
                else:
                    st.caption("Không có poster")

    

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
            "results/rating_distribution.png",
            width=600
        )
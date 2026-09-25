import streamlit as st
import pandas as pd
from recommender import get_movie_poster, get_recommendations_with_scores

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

    dark_mode = st.toggle(
        "🌙 Chế độ tối",
        value=st.session_state.dark_mode
    )

    st.session_state.dark_mode = dark_mode

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
def load_movie_poster(movie_title):
    return get_movie_poster(movie_title)

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
        movie_list
    )

    if st.button("Hiển Thị Gợi Ý"):
        recommendations = get_recommendations_with_scores(
            movie_title=selected_movie,
            top_n=5
        )

        if (
            recommendations
            and isinstance(recommendations[0], str)
            and recommendations[0].startswith("Không tìm thấy phim")
        ):
            st.warning(recommendations[0])
        elif recommendations:
            st.success(f"Đề xuất cho phim: {selected_movie}")
            st.subheader("Các phim tương tự")
            result_columns = st.columns(min(len(recommendations), 5))
            for index, recommendation in enumerate(recommendations, start=1):
                with result_columns[(index - 1) % len(result_columns)]:
                    movie_title = recommendation["title"]
                    compatibility = recommendation["compatibility"]
                    st.write(f"{index}. {movie_title}")
                    st.caption(f"Độ tương thích: {compatibility:.1f}%")
                    poster_url = load_movie_poster(movie_title)
                    if poster_url:
                        st.image(poster_url, width=180)
                    else:
                        st.caption("Không có poster")
        else:
            st.warning("Không tìm thấy phim đề xuất.")

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

    # TÌM KIẾM PHIM

    st.subheader("Tra Cứu Phim")

    search_text = st.text_input(
        "Nhập tên phim để tìm kiếm:"
    )

    if search_text:

        search_result = movies[
            movies["MovieTitle"]
            .str.contains(
                search_text,
                case=False,
                na=False
            )
        ]

        st.write(
            f"Tìm thấy {len(search_result)} phim."
        )

        st.dataframe(
            search_result[
                [
                    "MovieID",
                    "MovieTitle",
                    "ReleaseDate",
                    "IMDbURL"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

    else:

        st.dataframe(
            movies.head(20),
            use_container_width=True,
            hide_index=True
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

    # DỮ LIỆU ĐÁNH GIÁ

    st.subheader("Dữ Liệu Đánh Giá")

    st.dataframe(
        ratings.head(20),
        use_container_width=True,
        hide_index=True
    )

    # KHU VỰC EDA CỦA TV3

    st.subheader("Biểu Đồ Phân Tích")
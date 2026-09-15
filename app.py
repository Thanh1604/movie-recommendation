import streamlit as st
from recommender import get_recommendations

st.set_page_config(page_title="Hệ Thống Đề Xuất Phim", layout="wide")
st.title("🎬 Hệ Thống Phân Tích & Đề Xuất Phim (MovieLens 100K)")

tab1, tab2 = st.tabs(["🔍 Gợi Ý Phim", "📊 Phân Tích Dữ Liệu (EDA)"])

with tab1:
    st.header("Tìm Phim Tương Tự")
    selected_movie = st.text_input("Nhập tên bộ phim bạn thích:", "Toy Story (1995)")
    num_rec = st.slider("Số lượng phim gợi ý:", 1, 10, 5)
    
    if st.button("Hiển Thị Gợi Ý"):
        results = get_recommendations(selected_movie, num_rec)
        st.subheader("Các bộ phim tương tự:")
        for i, movie in enumerate(results, 1):
            st.write(f"**{i}.** {movie}")

with tab2:
    st.header("Phân Tích Dữ Liệu")
    st.info("Khu vực hiển thị biểu đồ của TV3")
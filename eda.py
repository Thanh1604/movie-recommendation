import os
import pandas as pd
import matplotlib.pyplot as plt


# =========================================================
# 1. PATH
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_PATH = os.path.join(BASE_DIR, "data")
RESULTS_PATH = os.path.join(BASE_DIR, "results")

RATINGS_FILE = os.path.join(DATA_PATH,"cleaned_ratings.csv")

MOVIES_FILE = os.path.join(DATA_PATH,"cleaned_movies.csv")
os.makedirs(RESULTS_PATH, exist_ok=True)

# =========================================================
# 2. GENRE COLUMNS
# =========================================================

GENRE_COLUMNS = [
    "Unknown",
    "Action",
    "Adventure",
    "Animation",
    "Children",
    "Comedy",
    "Crime",
    "Documentary",
    "Drama",
    "Fantasy",
    "FilmNoir",
    "Horror",
    "Musical",
    "Mystery",
    "Romance",
    "SciFi",
    "Thriller",
    "War",
    "Western"
]

# =========================================================
# 3. LOAD DATA
# =========================================================

def load_data():
    ratings = pd.read_csv(RATINGS_FILE)
    movies = pd.read_csv(MOVIES_FILE)
    return ratings, movies

# =========================================================
# 4. BASIC ANALYSIS
# =========================================================

def basic_analysis(ratings, movies):
    print("=" * 60)
    print("BASIC DATA INFORMATION")
    print("=" * 60)
    # -------------------------
    # Ratings
    # -------------------------
    print("\n--- Ratings ---")
    print("Shape:", ratings.shape)
    print("\nColumns:")
    print(ratings.columns.tolist())
    print("\nData types:")
    print(ratings.dtypes)
    print("\nMissing values:")
    print(ratings.isnull().sum())
    print("\nNumber of duplicated rows:")
    print(ratings.duplicated().sum())
    # -------------------------
    # Movies
    # -------------------------
    print("\n--- Movies ---")
    print("Shape:", movies.shape)
    print("\nColumns:")
    print(movies.columns.tolist())
    print("\nData types:")
    print(movies.dtypes)
    print("\nMissing values:")
    print(movies.isnull().sum())
    print("\nNumber of duplicated rows:")
    print(movies.duplicated().sum())
    # -------------------------
    # General information
    # -------------------------

    print("\n--- General Information ---")
    print("Number of users:",ratings["UserID"].nunique())
    print("Number of movies:",movies["MovieID"].nunique())
    print("Number of ratings:",len(ratings))

# =========================================================
# 5. RATING ANALYSIS
# =========================================================

def rating_analysis(ratings):

    print("\n" + "=" * 60)
    print("RATING ANALYSIS")
    print("=" * 60)
    # Số lượng rating theo từng mức điểm
    rating_count = (ratings["Ratings"].value_counts().sort_index())
    print("\nNumber of ratings for each score:")
    print(rating_count)
    # Tỷ lệ phần trăm
    rating_percent = (rating_count / len(ratings) * 100).round(2)
    print("\nPercentage of each score:")
    print(rating_percent)
    # Rating trung bình
    avg_rating = ratings["Ratings"].mean()
    print("\nAverage rating:",round(avg_rating, 2))
    return rating_count

# =========================================================
# 6. RATING VISUALIZATION
# =========================================================

def plot_rating_distribution(rating_count):
    plt.figure(figsize=(8, 5))
    rating_count.plot(kind="bar",edgecolor="black",linewidth=1)
    plt.title("Distribution of Movie Ratings")
    plt.xlabel("Rating")
    plt.ylabel("Number of Ratings")
    plt.xticks(rotation=0)
    plt.tight_layout()
    # Lưu biểu đồ
    output_file = os.path.join(RESULTS_PATH,"rating_distribution.png")
    plt.savefig(output_file,dpi=300)
    print("\nSaved:",output_file)
    plt.show()
    plt.close()

# =========================================================
# 7. MOVIE ANALYSIS
# =========================================================

def movie_analysis(ratings, movies):

    print("\n" + "=" * 60)
    print("MOVIE ANALYSIS")
    print("=" * 60)

    # Tính số lượng rating và rating trung bình
    movie_stats = (ratings.groupby("MovieID").agg(RatingCount=("Ratings", "count"),
                    AvgRating=("Ratings", "mean")).reset_index())

    # Làm tròn rating trung bình
    movie_stats["AvgRating"] = (movie_stats["AvgRating"].round(2))
    # Ghép tên phim
    movie_stats = movie_stats.merge(movies[["MovieID", "MovieTitle"]],on="MovieID",how="left")

    # Top 10 phim có nhiều rating nhất
    top_movies = (movie_stats.sort_values("RatingCount",ascending=False).head(10))

    print("\nTop 10 most rated movies:")
    print(top_movies[["MovieTitle","RatingCount","AvgRating"]].to_string(index=False))
    return movie_stats

# =========================================================
# 8. MOVIE VISUALIZATION
# =========================================================

def plot_top_movies(movie_stats):

    # Lấy top 10
    top_movies = (movie_stats.sort_values("RatingCount",ascending=False).head(10).sort_values("RatingCount"))
    plt.figure(figsize=(10, 6))
    plt.barh(top_movies["MovieTitle"],top_movies["RatingCount"],edgecolor="black",linewidth=1)
    plt.title("Top 10 Most Rated Movies")
    plt.xlabel("Number of Ratings")
    plt.ylabel("Movie")
    plt.tight_layout()

    # Lưu biểu đồ
    output_file = os.path.join(RESULTS_PATH,"top_10_most_rated_movies.png")
    plt.savefig(output_file,dpi=300)
    print("\nSaved:",output_file)
    plt.show()
    plt.close()

# =========================================================
# 9. GENRE ANALYSIS
# =========================================================

def genre_analysis(movies):
    print("\n" + "=" * 60)
    print("GENRE ANALYSIS")
    print("=" * 60)
    # Đếm số phim của từng genre
    genre_count = (movies[GENRE_COLUMNS].sum().sort_values(ascending=False))
    print("\nNumber of movies by genre:")
    print(genre_count)
    return genre_count

# =========================================================
# 10. GENRE VISUALIZATION
# =========================================================

def plot_genre_distribution(genre_count):
    plt.figure(figsize=(10, 6))
    genre_count.plot(kind="bar")
    plt.title("Number of Movies by Genre")
    plt.xlabel("Genre")
    plt.ylabel("Number of Movies")
    plt.xticks(rotation=45)
    plt.tight_layout()
    # Lưu biểu đồ
    output_file = os.path.join(RESULTS_PATH,"genre_distribution.png")
    plt.savefig(output_file,dpi=300)
    print("\nSaved:",output_file)
    plt.show()
    plt.close()

# =========================================================
# 11. USER ANALYSIS
# =========================================================

def user_analysis(ratings):
    print("\n" + "=" * 60)
    print("USER ANALYSIS")
    print("=" * 60)

    # Số lượng rating của mỗi user
    user_rating_count = (ratings.groupby("UserID").size().sort_values(ascending=False))
    print("\nTop 10 most active users:")
    print(user_rating_count.head(10))
    # Rating trung bình của từng user
    user_avg_rating = (ratings.groupby("UserID")["Ratings"].mean())
    print("\nStatistics of average rating per user:")
    print(user_avg_rating.describe())
    return (user_rating_count,user_avg_rating)

# =========================================================
# 12. USER VISUALIZATION
# =========================================================

def plot_user_activity(user_rating_count):
    # Top 10 user
    top_users = (user_rating_count.head(10).sort_values())
    plt.figure(figsize=(8, 5))
    plt.barh(top_users.index.astype(str),top_users.values)
    plt.title("Top 10 Most Active Users")
    plt.xlabel("Number of Ratings")
    plt.ylabel("UserID")
    plt.tight_layout()
    # Lưu biểu đồ
    output_file = os.path.join(RESULTS_PATH,"top_10_active_users.png")
    plt.savefig(output_file,dpi=300)
    print("\nSaved:",output_file)
    plt.show()
    plt.close()

# =========================================================
# 13. GENRE RATING ANALYSIS
# =========================================================

def genre_rating_analysis(ratings, movies):
    print("\n" + "=" * 60)
    print("GENRE RATING ANALYSIS")
    print("=" * 60)
    results = []
    for genre in GENRE_COLUMNS:
        # Bỏ Unknown
        if genre == "Unknown":
            continue
        # Lấy MovieID thuộc genre
        movie_ids = movies.loc[movies[genre] == 1,"MovieID"]
        # Lấy rating của các movie đó
        genre_ratings = ratings[ratings["MovieID"].isin(movie_ids)]
        results.append({"Genre": genre,"MovieCount": len(movie_ids),"RatingCount": len(genre_ratings),
            "AvgRating": genre_ratings["Ratings"].mean()})
    genre_stats = pd.DataFrame(results)
    genre_stats["AvgRating"] = (genre_stats["AvgRating"].round(2))
    print("\nGenre statistics:")
    print(genre_stats.sort_values("RatingCount",ascending=False).to_string(index=False))
    return genre_stats


# =========================================================
# 14. GENRE RATING COUNT VISUALIZATION
# =========================================================

def plot_genre_rating_count(genre_stats):
    data = (genre_stats.sort_values("RatingCount",ascending=True))
    plt.figure(figsize=(10, 6))
    plt.barh(data["Genre"],data["RatingCount"])
    plt.title("Number of Ratings by Genre")
    plt.xlabel("Number of Ratings")
    plt.ylabel("Genre")
    plt.tight_layout()
    output_file = os.path.join(RESULTS_PATH,"rating_count_by_genre.png")
    plt.savefig(output_file,dpi=300)
    print("\nSaved:",output_file)
    plt.show()
    plt.close()

# =========================================================
# 15. GENRE AVERAGE RATING VISUALIZATION
# =========================================================

def plot_genre_average_rating(genre_stats):
    data = (genre_stats.sort_values("AvgRating",ascending=True))
    plt.figure(figsize=(10, 6))
    plt.barh(data["Genre"],data["AvgRating"])
    plt.title("Average Rating by Genre")
    plt.xlabel("Average Rating")
    plt.ylabel("Genre")
    plt.xlim(0, 5)
    plt.tight_layout()
    output_file = os.path.join(RESULTS_PATH,"average_rating_by_genre.png")
    plt.savefig(output_file,dpi=300)
    print("\nSaved:",output_file)
    plt.show()
    plt.close()

# =========================================================
# 16. USER BEHAVIOR ANALYSIS
# =========================================================

def user_behavior_analysis(ratings):
    print("\n" + "=" * 60)
    print("USER BEHAVIOR ANALYSIS")
    print("=" * 60)
    user_stats = (ratings.groupby("UserID").agg(RatingCount=("Ratings", "count"),
            AvgRating=("Ratings", "mean")).reset_index())
    user_stats["AvgRating"] = (user_stats["AvgRating"].round(2))
    print("\nUser statistics:")
    print(user_stats.describe())
    print("\nUsers with most ratings:")
    print(user_stats.sort_values("RatingCount",ascending=False).head(10).to_string(index=False))
    return user_stats

# =========================================================
# 17. USER ACTIVITY DISTRIBUTION
# =========================================================

def plot_user_activity_distribution(user_stats):
    plt.figure(figsize=(8, 5))
    plt.hist(user_stats["RatingCount"],bins=30,edgecolor="black",linewidth=1)
    plt.title("Distribution of Ratings per User")
    plt.xlabel("Number of Ratings per User")
    plt.ylabel("Number of Users")
    plt.tight_layout()
    output_file = os.path.join(RESULTS_PATH,"user_activity_distribution.png")
    plt.savefig(output_file,dpi=300)
    print("\nSaved:",output_file)
    plt.show()
    plt.close()

# =========================================================
# 18. USER AVERAGE RATING DISTRIBUTION
# =========================================================

def plot_user_average_rating(user_stats):
    plt.figure(figsize=(8, 5))
    plt.hist(user_stats["AvgRating"],bins=20,edgecolor="black",linewidth=1)
    plt.title("Distribution of Average Rating per User")
    plt.xlabel("Average Rating")
    plt.ylabel("Number of Users")
    plt.xlim(1, 5)
    plt.tight_layout()
    output_file = os.path.join(RESULTS_PATH,"user_average_rating_distribution.png")
    plt.savefig(output_file,dpi=300)
    print("\nSaved:",output_file)
    plt.show()
    plt.close()

# =========================================================
# 19. MOVIE RATING ANALYSIS
# =========================================================

def movie_rating_analysis(movie_stats):
    print("\n" + "=" * 60)
    print("MOVIE RATING ANALYSIS")
    print("=" * 60)
    print("\nMovie statistics:")
    print(movie_stats[["RatingCount","AvgRating"]].describe())
    return movie_stats

# =========================================================
# 20. MOVIE POPULARITY DISTRIBUTION
# =========================================================

def plot_movie_rating_count_distribution(movie_stats):
    plt.figure(figsize=(8, 5))
    plt.hist(movie_stats["RatingCount"],bins=30)
    plt.title("Distribution of Ratings per Movie")
    plt.xlabel("Number of Ratings per Movie")
    plt.ylabel("Number of Movies")
    plt.tight_layout()
    output_file = os.path.join(RESULTS_PATH,"movie_rating_count_distribution.png")
    plt.savefig(output_file,dpi=300)
    print("\nSaved:",output_file)
    plt.show()
    plt.close()

# =========================================================
# 21. MOVIE AVERAGE RATING DISTRIBUTION
# =========================================================

def plot_movie_average_rating_distribution(movie_stats):
    plt.figure(figsize=(8, 5))
    plt.hist(movie_stats["AvgRating"],bins=20)
    plt.title("Distribution of Average Movie Ratings")
    plt.xlabel("Average Rating")
    plt.ylabel("Number of Movies")
    plt.xlim(1, 5)
    plt.tight_layout()
    output_file = os.path.join(RESULTS_PATH,"movie_average_rating_distribution.png")
    plt.savefig(output_file,dpi=300)
    print("\nSaved:",output_file)
    plt.show()
    plt.close()

# =========================================================
# 22. TIME ANALYSIS
# =========================================================

def time_analysis(ratings):
    print("\n" + "=" * 60)
    print("TIME ANALYSIS")
    print("=" * 60)
    ratings = ratings.copy()
    ratings["Timestamp"] = pd.to_datetime(ratings["Timestamp"])
    ratings["Year"] = (ratings["Timestamp"].dt.year)
    ratings["Month"] = (ratings["Timestamp"].dt.month)
    # Rating theo năm
    yearly_rating_count = (ratings.groupby("Year").size())
    print("\nNumber of ratings by year:")
    print(yearly_rating_count)
    return ratings, yearly_rating_count

# =========================================================
# 23. YEARLY RATING VISUALIZATION
# =========================================================

def plot_yearly_ratings(yearly_rating_count):
    plt.figure(figsize=(8, 5))
    yearly_rating_count.plot(kind="bar")
    plt.title("Number of Ratings by Year")
    plt.xlabel("Year")
    plt.ylabel("Number of Ratings")
    plt.xticks(rotation=0)
    plt.tight_layout()
    output_file = os.path.join(RESULTS_PATH,"ratings_by_year.png")
    plt.savefig(output_file,dpi=300)
    print("\nSaved:",output_file)
    plt.show()
    plt.close()

# =========================================================
# 24. AVERAGE RATING BY YEAR
# =========================================================

def plot_average_rating_by_year(ratings):
    yearly_avg = (ratings.groupby("Year")["Ratings"].mean())
    plt.figure(figsize=(8, 5))
    plt.plot(yearly_avg.index,yearly_avg.values,marker="o")

    plt.title("Average Rating by Year")
    plt.xlabel("Year")

    plt.ylabel("Average Rating")

    plt.ylim(1, 5)
    plt.grid(True)
    plt.tight_layout()

    output_file = os.path.join(RESULTS_PATH,"average_rating_by_year.png")

    plt.savefig(output_file,dpi=300)
    print("\nSaved:",output_file)
    plt.show()
    plt.close()

# =========================================================
# 25. USER-MOVIE SPARSITY
# =========================================================

def sparsity_analysis(ratings,movies):
    print("\n" + "=" * 60)
    print("USER-MOVIE SPARSITY")
    print("=" * 60)

    num_users = ratings["UserID"].nunique()
    num_movies = movies["MovieID"].nunique()
    num_ratings = len(ratings)

    total_possible = (num_users * num_movies)

    density = (num_ratings / total_possible)

    sparsity = 1 - density
    print("Number of users:",num_users)

    print("Number of movies:",num_movies)
    print("Actual ratings:",num_ratings)

    print("Possible user-movie pairs:",total_possible)

    print("Density:",round(density * 100, 2),"%")
    print("Sparsity:",round(sparsity * 100, 2),"%")
    return density, sparsity

# =========================================================
# 26. MOVIE RATING QUALITY
# =========================================================

def movie_rating_quality(
    movie_stats
):

    print("\n" + "=" * 60)
    print("MOVIE RATING QUALITY")
    print("=" * 60)

    print("\nMovies with fewer than 10 ratings:")

    print((movie_stats[movie_stats["RatingCount"] < 10].shape[0]))

    print("\nMovies with fewer than 20 ratings:")

    print((movie_stats[movie_stats["RatingCount"] < 20].shape[0]))
    print("\nMovies with at least 100 ratings:")
    print((movie_stats[movie_stats["RatingCount"] >= 100].shape[0]))
    return movie_stats

# =========================================================
# 27. HIGH-RATED MOVIES WITH ENOUGH RATINGS
# =========================================================

def top_rated_movies(movie_stats,min_ratings=50):

    print("\n" + "=" * 60)
    print("TOP RATED MOVIES")
    print("=" * 60)
    filtered = movie_stats[movie_stats["RatingCount"] >= min_ratings]
    top_movies = (filtered.sort_values("AvgRating",ascending=False).head(10))
    print(f"\nTop movies with at least "f"{min_ratings} ratings:")
    print(top_movies[["MovieTitle","RatingCount","AvgRating"]].to_string(index=False))
    return top_movies


def plot_top_weighted_movies(movie_stats, ratings, min_ratings=50):
    # Điểm trung bình của toàn bộ các lượt đánh giá
    C = ratings["Ratings"].mean()

    # Chỉ xét những phim có đủ số lượt đánh giá
    m = min_ratings
    eligible_movies = movie_stats[
        movie_stats["RatingCount"] >= min_ratings
    ].copy()

    if eligible_movies.empty:
        print("Không có phim nào đủ số lượt đánh giá.")
        return

    # Tính Weighted Rating
    v = eligible_movies["RatingCount"]
    R = eligible_movies["AvgRating"]

    eligible_movies["WeightedRating"] = (
        (v / (v + m)) * R
        + (m / (v + m)) * C
    )

    # Lấy Top 10 theo Weighted Rating
    top10 = eligible_movies.sort_values(
        "WeightedRating", ascending=False
    ).head(10)

    # Đảo thứ tự để phim đứng đầu hiển thị ở trên cùng
    top10 = top10.sort_values("WeightedRating")

    # Vẽ biểu đồ
    plt.figure(figsize=(12, 7))

    bars = plt.barh(
        top10["MovieTitle"],
        top10["WeightedRating"],
        color="steelblue",
        edgecolor="black"
    )

    # Hiển thị điểm và số lượt đánh giá
    for bar, (_, row) in zip(bars, top10.iterrows()):
        label = (
            f' WR: {row["WeightedRating"]:.2f}'
            f' | Avg: {row["AvgRating"]:.2f}'
            f' | n={int(row["RatingCount"])}'
        )

        plt.text(
            bar.get_width() + 0.02,
            bar.get_y() + bar.get_height() / 2,
            label,
            va="center",
            fontsize=8
        )

    plt.title("Top 10 Highest-Rated Movies (Weighted Rating)")
    plt.xlabel("Weighted Rating")
    plt.ylabel("Movie")
    plt.xlim(0, 5.8)
    plt.tight_layout()
    os.makedirs("results", exist_ok=True)
    plt.savefig(
        "results/top_10_highest_rated_movies.png",
        dpi=300,
        bbox_inches="tight"
    )

    plt.show()
    plt.close()

    print("\nTop 10 phim có Weighted Rating cao nhất:")
    print(
        top10[
            ["MovieTitle", "AvgRating", "RatingCount", "WeightedRating"]
        ].sort_values("WeightedRating", ascending=False).to_string(index=False)
    )


def main():
    # =====================================================
    # LOAD DATA
    # =====================================================

    ratings, movies = load_data()

    # =====================================================
    # BASIC
    # =====================================================

    basic_analysis(ratings,movies)

    # =====================================================
    # RATING
    # =====================================================
    rating_count = rating_analysis(ratings)
    plot_rating_distribution(rating_count)

    # =====================================================
    # MOVIE
    # =====================================================

    movie_stats = movie_analysis(ratings,movies)
    plot_top_movies(movie_stats)
    plot_top_weighted_movies(movie_stats,ratings,min_ratings=50)
    movie_rating_analysis(movie_stats)
    plot_movie_rating_count_distribution(movie_stats)
    plot_movie_average_rating_distribution(movie_stats)
    movie_rating_quality(movie_stats)
    top_rated_movies(movie_stats,min_ratings=50)
    # =====================================================
    # GENRE
    # =====================================================

    genre_count = genre_analysis(movies)
    plot_genre_distribution(genre_count)
    genre_stats = genre_rating_analysis(ratings,movies)
    plot_genre_rating_count(genre_stats)
    plot_genre_average_rating(genre_stats)

    # =====================================================
    # USER
    # =====================================================

    user_rating_count, user_avg_rating = (user_analysis(ratings))
    plot_user_activity(user_rating_count)
    user_stats = user_behavior_analysis(ratings)
    plot_user_activity_distribution(user_stats)
    plot_user_average_rating(user_stats)

    # =====================================================
    # TIME
    # =====================================================

    ratings, yearly_rating_count = (time_analysis(ratings))
    plot_yearly_ratings(yearly_rating_count)
    plot_average_rating_by_year(ratings)

    # =====================================================
    # SPARSITY
    # =====================================================

    sparsity_analysis(ratings,movies)

if __name__ == "__main__":
    main()
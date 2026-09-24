import pandas as pd
import numpy as np
import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD


def load_local_api_key():
    """Read TMDB_API_KEY from the local .env file when available."""
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(env_path):
        return

    with open(env_path, encoding="utf-8") as env_file:
        for line in env_file:
            name, separator, value = line.strip().partition("=")
            if separator and name == "TMDB_API_KEY":
                os.environ.setdefault(name, value.strip().strip('"').strip("'"))
                return


load_local_api_key()

class HybridRecommender:
    def __init__(self, movies_path='data/cleaned_movies.csv', ratings_path='data/cleaned_ratings.csv'):
        # 1. Load dữ liệu
        self.movies = pd.read_csv(movies_path)
        self.ratings = pd.read_csv(ratings_path)
        
        # 2. Xác định danh sách cột thể loại
        exclude_cols = ["MovieID", "MovieTitle", "ReleaseDate", "IMDbURL", "Genres", "UserID", "Ratings", "Timestamp"]
        self.genre_cols = [col for col in self.movies.columns if col not in exclude_cols]
        
        # 3. Giai đoạn 1: Content-Based (Cosine Similarity trên thể loại)
        genre_matrix = self.movies[self.genre_cols].values
        self.content_sim = cosine_similarity(genre_matrix, genre_matrix)
        
        # 4. Giai đoạn 2: Collaborative Filtering (TruncatedSVD)
        user_item_matrix = self.ratings.pivot_table(index='UserID', columns='MovieID', values='Ratings').fillna(0)
        
        n_components = min(20, user_item_matrix.shape[1] - 1)
        self.svd = TruncatedSVD(n_components=n_components, random_state=42)
        user_item_predicted = self.svd.fit_transform(user_item_matrix)
        
        self.predicted_ratings = pd.DataFrame(
            np.dot(user_item_predicted, self.svd.components_),
            index=user_item_matrix.index,
            columns=user_item_matrix.columns
        )

    def recommend(self, movie_title, user_id=1, top_n=5):
        recommendations = self.recommend_with_scores(movie_title, user_id, top_n)
        if recommendations and isinstance(recommendations[0], str):
            return recommendations
        return [recommendation['title'] for recommendation in recommendations]

    def recommend_with_scores(self, movie_title, user_id=1, top_n=5):
        # Tìm phim theo tên
        movie_row = self.movies[self.movies['MovieTitle'].str.lower() == movie_title.lower()]
        
        if movie_row.empty:
            movie_row = self.movies[self.movies['MovieTitle'].str.lower().str.contains(movie_title.lower(), na=False)]
            if movie_row.empty:
                return [f"Không tìm thấy phim '{movie_title}'!"]
        
        idx = movie_row.index[0]
        
        # Content-Based: Top 30 tương đồng
        sim_scores = list(enumerate(self.content_sim[idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        top_candidates = sim_scores[1:31]
        
        candidate_indices = [i[0] for i in top_candidates]
        candidate_movies = self.movies.iloc[candidate_indices].copy()
        candidate_movies['Compatibility'] = [
            self.content_sim[idx][candidate_idx]
            for candidate_idx in candidate_indices
        ]
        
        # Collaborative: Dự đoán rating
        predicted_scores = []
        for _, row in candidate_movies.iterrows():
            m_id = row['MovieID']
            if user_id in self.predicted_ratings.index and m_id in self.predicted_ratings.columns:
                score = self.predicted_ratings.loc[user_id, m_id]
            else:
                score = 3.0
            predicted_scores.append(score)
            
        candidate_movies['PredictedRating'] = predicted_scores
        
        # Sắp xếp và trả về
        final_recommendations = candidate_movies.sort_values(by='PredictedRating', ascending=False)
        recommendations = final_recommendations.head(top_n)
        return [
            {
                'title': remove_release_year(row['MovieTitle']),
                'compatibility': round(float(row['Compatibility']) * 100, 1),
            }
            for _, row in recommendations.iterrows()
        ]

recommender_system = HybridRecommender()

def get_recommendations(movie_title, user_id=1, top_n=5):
    return recommender_system.recommend(movie_title, user_id, top_n)


def get_recommendations_with_scores(movie_title, user_id=1, top_n=5):
    return recommender_system.recommend_with_scores(movie_title, user_id, top_n)

def get_all_movie_titles():
    return [remove_release_year(title) for title in recommender_system.movies['MovieTitle'].tolist()]


def remove_release_year(movie_title):
    """Remove a trailing release year, such as '(1995)', from a movie title."""
    return re.sub(r"\s*\(\d{4}\)\s*$", "", str(movie_title)).strip()


def get_movie_poster(movie_title, api_key=None):
    """Return the TMDB poster URL for a movie, or None when unavailable."""
    api_key = api_key or os.getenv("TMDB_API_KEY")
    movie_title = remove_release_year(movie_title) if movie_title else ""
    if not api_key or not movie_title:
        return None

    params = urlencode({
        "api_key": api_key,
        "query": movie_title,
        "language": "en-US",
        "include_adult": "false",
    })
    search_url = f"https://api.themoviedb.org/3/search/movie?{params}"

    try:
        with urlopen(search_url, timeout=10) as response:
            data = json.load(response)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return None

    results = data.get("results", [])
    if not results or not results[0].get("poster_path"):
        return None

    return f"https://image.tmdb.org/t/p/w500{results[0]['poster_path']}"
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD

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
        return final_recommendations['MovieTitle'].head(top_n).tolist()

recommender_system = HybridRecommender()

def get_recommendations(movie_title, user_id=1, top_n=5):
    return recommender_system.recommend(movie_title, user_id, top_n)

def get_all_movie_titles():
    return recommender_system.movies['MovieTitle'].tolist()
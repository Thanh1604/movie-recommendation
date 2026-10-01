import pandas as pd

# ============================================
# CONFIG
# ============================================

DATA_PATH = "data/"

RATINGS_FILE = DATA_PATH + "u.data"
MOVIES_FILE = DATA_PATH + "u.item"

CLEANED_RATINGS_FILE = DATA_PATH + "cleaned_ratings.csv"
CLEANED_MOVIES_FILE = DATA_PATH + "cleaned_movies.csv"

RATINGS_COLUMNS = [
    "UserID",
    "MovieID",
    "Ratings",
    "Timestamp"
]

MOVIES_COLUMNS = [
    "MovieID",
    "MovieTitle",
    "ReleaseDate",
    "VideoReleaseDate",
    "IMDbURL",
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

# =============================================
# load data: load_ratings, load_movie
# =============================================

def load_ratings():
    ratings = pd.read_csv(
        RATINGS_FILE,
        sep= "\t",
        names= RATINGS_COLUMNS
    )
    return ratings


def load_movies():
    movies = pd.read_csv(
        MOVIES_FILE,
        sep= "|",
        names= MOVIES_COLUMNS,
        encoding= "latin-1"
    )
    return movies


# inspect_data kiem tra du lieu dau vao

def inspect_data(df, name):
    print("\n==============================")
    print(name)
    print("==============================")

    print("Shape:", df.shape)

    print("\nColumns:")
    print(df.columns.tolist())

    print("\nMissing values:")
    print(df.isnull().sum())

    print("\nDuplicate rows:")
    print(df.duplicated().sum())

    print("\nData types:")
    print(df.dtypes)

# Process data_ratings

def clean_ratings(ratings):
    ratings = ratings.drop_duplicates()
    return ratings

def clean_movies(movies):
    movies = movies.drop_duplicates()
    movies["ReleaseDate"] = movies["ReleaseDate"].fillna("Unknown")
    movies["IMDbURL"] = movies["IMDbURL"].fillna("Unknown")
    movies = movies.drop(columns=["VideoReleaseDate"])
    return movies

# Process

def process_timestamp(ratings):
    ratings["Timestamp"] = pd.to_datetime(
        ratings["Timestamp"],
        unit= "s"
    )
    return ratings

def process_genres(movies):
    def get_genres(row):
        genres = []
        for genre in GENRE_COLUMNS:
            if row[genre] == 1:
                genres.append(genre)
        return ' | '.join(genres)
    movies["Genres"] = movies.apply(
        get_genres,
        axis = 1
    )
    return movies


# Kiem tra du lieu sau khi lam sach

def validate_data(df, name):
    print("\n==============================")
    print("VALIDATE:", name)
    print("==============================")
    print("Shape:", df.shape)
    print("\nMissing:")
    print(df.isnull().sum())
    print("\nDuplicates:")
    print(df.duplicated().sum())

# Xuat du lieu: save_data

def save_data(movies, ratings):
    movies.to_csv(
        CLEANED_MOVIES_FILE,
        index = False
    )
    ratings.to_csv(
        CLEANED_RATINGS_FILE,
        index = False
    )

# main

def main():
    ratings = load_ratings()
    movies = load_movies()

    inspect_data(ratings, "Ratings")
    inspect_data(movies, "Movies")

    ratings = clean_ratings(ratings)
    movies = clean_movies(movies)

    ratings = process_timestamp(ratings)
    movies = process_genres(movies)

    validate_data(ratings, "Cleaned Ratings")
    validate_data(movies, "Cleaned Movies")

    save_data(movies, ratings)

if __name__ == "__main__":
    main()

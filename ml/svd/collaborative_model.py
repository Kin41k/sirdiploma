"""
Surprise SVD collaborative filtering model.
Uses synthetic user ratings generated during DB seeding.
"""
import pickle
from pathlib import Path

from surprise import SVD, Dataset, Reader
from surprise.model_selection import train_test_split as surprise_split
import pandas as pd

MODELS_DIR = Path(__file__).parent.parent / "models"


def load_ratings_from_db(db_path: str) -> pd.DataFrame:
    import sqlite3
    conn = sqlite3.connect(db_path)
    df = pd.read_sql(
        "SELECT user_id, movie_id, rating FROM ratings",
        conn,
    )
    conn.close()
    print(f"[svd] Loaded {len(df)} ratings from DB")
    return df


def train_svd(ratings_df: pd.DataFrame, n_factors: int = 100, n_epochs: int = 20) -> SVD:
    reader = Reader(rating_scale=(0.5, 5.0))
    data = Dataset.load_from_df(ratings_df[["user_id", "movie_id", "rating"]], reader)

    trainset, testset = surprise_split(data, test_size=0.15, random_state=42)

    algo = SVD(n_factors=n_factors, n_epochs=n_epochs, lr_all=0.005, reg_all=0.02, random_state=42)
    algo.fit(trainset)

    predictions = algo.test(testset)
    rmse = _compute_rmse(predictions)
    print(f"[svd] Trained. RMSE on test set: {rmse:.4f} | factors={n_factors} epochs={n_epochs}")

    return algo, rmse


def _compute_rmse(predictions) -> float:
    import math
    squared_errors = [(pred.r_ui - pred.est) ** 2 for pred in predictions]
    return math.sqrt(sum(squared_errors) / len(squared_errors))


def save_model(algo: SVD) -> None:
    MODELS_DIR.mkdir(exist_ok=True)
    with open(MODELS_DIR / "svd_model.pkl", "wb") as f:
        pickle.dump(algo, f)
    print(f"[svd] Model saved to {MODELS_DIR / 'svd_model.pkl'}")

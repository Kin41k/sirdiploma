"""
Train SVD and save to ml/models/.
Called by ml/main.py — receives the movies DataFrame so it never
needs to go to disk for movie data. Falls back to synthetic ratings
if the application DB has no ratings yet.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

import pandas as pd
from ml.svd.collaborative_model import (
    load_ratings_from_db,
    generate_synthetic_ratings,
    train_svd,
    save_model,
)

DB_PATH = ROOT / "backend" / "data" / "cinemadb.db"
MIN_RATINGS = 50


def run(movies_df: pd.DataFrame = None):
    """
    Train SVD.  movies_df is passed from ml/main.py so we can
    generate synthetic ratings without re-reading the CSV.
    """
    ratings_df = pd.DataFrame(columns=["user_id", "movie_id", "rating"])

    # Try DB first
    if DB_PATH.exists():
        ratings_df = load_ratings_from_db(str(DB_PATH))

    # Fall back to synthetic generation from movie data
    if len(ratings_df) < MIN_RATINGS:
        if movies_df is None or len(movies_df) == 0:
            print("[svd] No movies_df provided and DB empty — cannot train SVD.")
            return None
        print(f"[svd] DB has only {len(ratings_df)} ratings → generating synthetic ratings from CSV…")
        ratings_df = generate_synthetic_ratings(movies_df)

    algo, rmse_val = train_svd(ratings_df)
    save_model(algo)
    return rmse_val


if __name__ == "__main__":
    # Standalone usage: load CSV manually
    from ml.preprocessing.load_data import load_movies
    df = load_movies()
    run(df)

"""
Offline evaluation of the hybrid recommendation system.
Uses leave-one-out: hide last rating per user, recommend, measure.
"""
import sys
import json
import random
import pickle
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import load_npz

from ml.evaluation.metrics import average_metrics, rmse

DB_PATH = ROOT / "backend" / "data" / "cinemadb.db"
MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
K = 10
SAMPLE_USERS = 200
MIN_RATINGS_PER_USER = 10


def _load_ratings() -> pd.DataFrame:
    """Load ratings from DB, or return empty DataFrame."""
    if not DB_PATH.exists():
        return pd.DataFrame(columns=["user_id", "movie_id", "rating"])
    try:
        import sqlite3
        conn = sqlite3.connect(str(DB_PATH))
        df = pd.read_sql("SELECT user_id, movie_id, rating FROM ratings", conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame(columns=["user_id", "movie_id", "rating"])


def _load_models():
    """Load TF-IDF and SVD models. Returns (matrix, movie_ids, id_to_idx, algo)."""
    matrix, movie_ids, id_to_idx, algo = None, [], {}, None

    tfidf_path = MODELS_DIR / "tfidf_matrix.npz"
    ids_path = MODELS_DIR / "movie_ids.pkl"
    svd_path = MODELS_DIR / "svd_model.pkl"

    if tfidf_path.exists() and ids_path.exists():
        matrix = load_npz(tfidf_path).toarray()
        with open(ids_path, "rb") as f:
            movie_ids = pickle.load(f)
        id_to_idx = {mid: i for i, mid in enumerate(movie_ids)}

    if svd_path.exists():
        with open(svd_path, "rb") as f:
            algo = pickle.load(f)

    return matrix, movie_ids, id_to_idx, algo


def evaluate():
    ratings = _load_ratings()
    matrix, movie_ids, id_to_idx, algo = _load_models()

    if matrix is None and algo is None:
        print("[eval] No models found in ml/models/ — skipping evaluation.")
        print("       Run ml/main.py first to train models.")
        return

    if len(ratings) < MIN_RATINGS_PER_USER * 5:
        # No real user ratings in DB — use synthetic ratings for evaluation
        print("[eval] No DB ratings found, evaluating on synthetic data…")
        from ml.svd.collaborative_model import generate_synthetic_ratings
        # Load a small subset of movies for quick evaluation
        try:
            from ml.preprocessing.load_data import load_movies
            df = load_movies()
            ratings = generate_synthetic_ratings(df, n_users=100)
        except Exception as e:
            print(f"[eval] Could not generate synthetic ratings: {e}")
            _save_dummy_metrics()
            return

    # Filter users with enough ratings
    user_counts = ratings.groupby("user_id").size()
    eligible = user_counts[user_counts >= MIN_RATINGS_PER_USER].index.tolist()
    if not eligible:
        print("[eval] Not enough users with sufficient ratings for evaluation.")
        _save_dummy_metrics()
        return

    if len(eligible) > SAMPLE_USERS:
        eligible = random.sample(eligible, SAMPLE_USERS)

    print(f"[eval] Evaluating on {len(eligible)} users (K={K})…")

    all_movie_ids = set(movie_ids) if movie_ids else set()
    users_data = []
    rmse_pairs = []

    for user_id in eligible:
        user_ratings = ratings[ratings["user_id"] == user_id].sort_values("movie_id")
        if len(user_ratings) < MIN_RATINGS_PER_USER:
            continue

        # Leave-last-out
        test_row = user_ratings.iloc[-1]
        train_rows = user_ratings.iloc[:-1]
        relevant = {int(test_row["movie_id"])}

        liked_ids = train_rows[train_rows["rating"] >= 3.5]["movie_id"].tolist()
        trained_ids = set(train_rows["movie_id"].tolist())
        candidates = list((all_movie_ids - trained_ids))[:500]
        if not candidates:
            continue

        # Score candidates
        scores = {}
        for mid in candidates:
            cf_score = cb_score = pop_score = 0.0

            if algo:
                try:
                    cf_score = algo.predict(str(user_id), str(mid)).est / 5.0
                except Exception:
                    pass

            if matrix is not None and liked_ids and mid in id_to_idx:
                liked_idx = [id_to_idx[m] for m in liked_ids if m in id_to_idx]
                if liked_idx:
                    profile = matrix[liked_idx].mean(axis=0).reshape(1, -1)
                    candidate_vec = matrix[id_to_idx[mid]].reshape(1, -1)
                    cb_score = float(cosine_similarity(profile, candidate_vec)[0][0])

            scores[mid] = 0.45 * cf_score + 0.40 * cb_score + 0.15 * pop_score

        recommended = sorted(scores, key=scores.get, reverse=True)
        users_data.append({"recommended": recommended, "relevant": relevant})

        if algo:
            try:
                pred = algo.predict(str(user_id), str(test_row["movie_id"])).est
                rmse_pairs.append((float(test_row["rating"]), pred))
            except Exception:
                pass

    if not users_data:
        print("[eval] No evaluation data generated.")
        _save_dummy_metrics()
        return

    result = average_metrics(users_data, k=K)
    if rmse_pairs:
        y_true, y_pred = zip(*rmse_pairs)
        result["rmse"] = round(rmse(list(y_true), list(y_pred)), 4)

    print("\n=== Evaluation Results ===")
    for key, val in result.items():
        print(f"  {key}: {val}")

    _save_metrics(result)
    print(f"\n[eval] Metrics saved → {MODELS_DIR / 'metrics.json'}")


def _save_metrics(data: dict) -> None:
    MODELS_DIR.mkdir(exist_ok=True)
    with open(MODELS_DIR / "metrics.json", "w") as f:
        json.dump(data, f, indent=2)


def _save_dummy_metrics() -> None:
    _save_metrics({
        f"precision_at_{K}": 0.0,
        f"recall_at_{K}": 0.0,
        f"ndcg_at_{K}": 0.0,
        "rmse": None,
    })


if __name__ == "__main__":
    evaluate()

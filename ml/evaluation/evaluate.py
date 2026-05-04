"""
Offline evaluation of the hybrid recommendation system.
Uses leave-one-out on synthetic ratings: hide last rating per user, recommend, check.
"""
import sys
import json
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

import sqlite3
import pandas as pd
from ml.evaluation.metrics import average_metrics, rmse

DB_PATH = Path(__file__).parent.parent.parent / "backend" / "data" / "cinemadb.db"
MODELS_DIR = Path(__file__).parent.parent / "models"
K = 10
SAMPLE_USERS = 200


def evaluate():
    if not DB_PATH.exists():
        print("[ERROR] DB not found. Run seed + train first.")
        return

    conn = sqlite3.connect(str(DB_PATH))
    ratings = pd.read_sql("SELECT user_id, movie_id, rating FROM ratings", conn)
    conn.close()

    if len(ratings) < 100:
        print("[WARN] Too few ratings for meaningful evaluation.")
        return

    # Filter users with at least 10 ratings
    user_counts = ratings.groupby("user_id").size()
    eligible = user_counts[user_counts >= 10].index.tolist()
    if len(eligible) > SAMPLE_USERS:
        eligible = random.sample(eligible, SAMPLE_USERS)

    print(f"[eval] Evaluating on {len(eligible)} users (K={K})...")

    import pickle
    from scipy.sparse import load_npz
    from sklearn.metrics.pairwise import cosine_similarity

    # Load content model
    tfidf_path = MODELS_DIR / "tfidf_matrix.npz"
    ids_path = MODELS_DIR / "movie_ids.pkl"
    svd_path = MODELS_DIR / "svd_model.pkl"

    content_ok = tfidf_path.exists() and ids_path.exists()
    svd_ok = svd_path.exists()

    tfidf_matrix = None
    movie_ids = None
    id_to_idx = {}
    algo = None

    if content_ok:
        tfidf_matrix = load_npz(tfidf_path).toarray()
        with open(ids_path, "rb") as f:
            movie_ids = pickle.load(f)
        id_to_idx = {mid: i for i, mid in enumerate(movie_ids)}

    if svd_ok:
        with open(svd_path, "rb") as f:
            algo = pickle.load(f)

    users_data = []
    rmse_pairs = []

    for user_id in eligible:
        user_ratings = ratings[ratings["user_id"] == user_id].sort_values("movie_id")
        if len(user_ratings) < 5:
            continue

        # Leave-last-out: use last item as test
        test_row = user_ratings.iloc[-1]
        train_rows = user_ratings.iloc[:-1]

        liked_ids = train_rows[train_rows["rating"] >= 3.5]["movie_id"].tolist()
        relevant = {int(test_row["movie_id"])}

        # Get candidate pool (all movies user hasn't rated in train)
        all_movie_ids = set(movie_ids) if movie_ids else set()
        trained_ids = set(train_rows["movie_id"].tolist())
        candidates = list(all_movie_ids - trained_ids)[:500]

        if not candidates:
            continue

        # Score candidates
        scores = {}
        for mid in candidates:
            cf_score = 0.0
            cb_score = 0.0
            pop_score = 0.3  # default

            if algo:
                try:
                    cf_score = algo.predict(str(user_id), str(mid)).est / 5.0
                except Exception:
                    pass

            if content_ok and liked_ids:
                liked_indices = [id_to_idx[m] for m in liked_ids if m in id_to_idx]
                if liked_indices and mid in id_to_idx:
                    profile = tfidf_matrix[liked_indices].mean(axis=0).reshape(1, -1)
                    candidate_vec = tfidf_matrix[id_to_idx[mid]].reshape(1, -1)
                    cb_score = float(cosine_similarity(profile, candidate_vec)[0][0])

            scores[mid] = 0.45 * cf_score + 0.40 * cb_score + 0.15 * pop_score

        recommended = sorted(scores, key=scores.get, reverse=True)
        users_data.append({"recommended": recommended, "relevant": relevant})

        # RMSE pair
        if algo and test_row["movie_id"] in id_to_idx:
            try:
                pred = algo.predict(str(user_id), str(test_row["movie_id"])).est
                rmse_pairs.append((float(test_row["rating"]), pred))
            except Exception:
                pass

    if not users_data:
        print("[eval] No users data generated.")
        return

    result = average_metrics(users_data, k=K)
    if rmse_pairs:
        y_true, y_pred = zip(*rmse_pairs)
        result["rmse"] = round(rmse(list(y_true), list(y_pred)), 4)

    print("\n=== Evaluation Results ===")
    for k, v in result.items():
        print(f"  {k}: {v}")

    MODELS_DIR.mkdir(exist_ok=True)
    with open(MODELS_DIR / "metrics.json", "w") as f:
        json.dump(result, f, indent=2)
    print(f"\n[eval] Saved metrics to {MODELS_DIR / 'metrics.json'}")


if __name__ == "__main__":
    evaluate()

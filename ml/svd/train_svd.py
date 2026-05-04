"""Train SVD model and save to ml/models/."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from ml.svd.collaborative_model import load_ratings_from_db, train_svd, save_model

DB_PATH = Path(__file__).parent.parent.parent / "backend" / "data" / "cinemadb.db"


def run():
    if not DB_PATH.exists():
        print(f"[ERROR] DB not found at {DB_PATH}. Run seed first.")
        return None

    ratings_df = load_ratings_from_db(str(DB_PATH))
    if len(ratings_df) < 100:
        print(f"[WARN] Only {len(ratings_df)} ratings in DB. Recommend seeding more data.")

    algo, rmse = train_svd(ratings_df)
    save_model(algo)
    return rmse


if __name__ == "__main__":
    run()

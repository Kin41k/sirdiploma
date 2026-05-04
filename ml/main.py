"""
CinemaRec ML Training Pipeline
Run from the project root:   python -m ml.main
Or from the ml/ directory:   python main.py
"""
import sys
from pathlib import Path

# Make sure both the project root and backend are in sys.path
ROOT = Path(__file__).resolve().parent.parent   # sirdiploma/
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from ml.preprocessing.load_data import load_movies
from ml.preprocessing.clean_data import build_text_field, filter_quality
from ml.embeddings.content_embeddings import build_embeddings
from ml.svd.train_svd import run as train_svd_run
from ml.evaluation.evaluate import evaluate


def main():
    print("=" * 55)
    print("  CinemaRec ML Training Pipeline")
    print("=" * 55)

    # ── Step 1: Load & clean ──────────────────────────────────
    print("\n--- Step 1: Load & Clean Data ---")
    df = load_movies()
    df = filter_quality(df, min_votes=10)
    df["combined_text"] = build_text_field(df)
    print(f"[main] Ready: {len(df)} movies  |  sample text: {df['combined_text'].iloc[0][:70]}…")

    # ── Step 2: Content embeddings (TF-IDF) ───────────────────
    print("\n--- Step 2: Content Embeddings (TF-IDF) ---")
    try:
        build_embeddings(df)
    except Exception as e:
        print(f"[ERROR] Content embeddings failed: {e}")
        print("        Backend will fall back to popularity-only recommendations.")

    # ── Step 3: Collaborative filtering (SVD) ─────────────────
    print("\n--- Step 3: Collaborative Filtering (SVD) ---")
    try:
        rmse_val = train_svd_run(df)
        if rmse_val is not None:
            print(f"[main] SVD RMSE: {rmse_val:.4f}")
    except Exception as e:
        print(f"[ERROR] SVD training failed: {e}")
        print("        Backend will skip collaborative scores.")

    # ── Step 4: Evaluation ────────────────────────────────────
    print("\n--- Step 4: Evaluation ---")
    try:
        evaluate()
    except Exception as e:
        print(f"[WARN] Evaluation failed: {e}")

    print("\n" + "=" * 55)
    print("  Training complete. Models saved to ml/models/")
    print("=" * 55)


if __name__ == "__main__":
    main()

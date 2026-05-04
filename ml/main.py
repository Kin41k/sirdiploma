"""
Full ML training pipeline.
Run: cd ml && python main.py

Steps:
1. Load CSV → clean → build combined text
2. Build TF-IDF matrix (content-based)
3. Train SVD (collaborative filtering)
4. Run evaluation → save metrics.json
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from ml.preprocessing.load_data import load_movies
from ml.preprocessing.clean_data import build_text_field, filter_quality
from ml.embeddings.content_embeddings import build_embeddings
from ml.svd.train_svd import run as train_svd_run
from ml.evaluation.evaluate import evaluate


def main():
    print("=" * 50)
    print("CinemaRec ML Training Pipeline")
    print("=" * 50)

    # Step 1: Load & clean data
    df = load_movies()
    df = filter_quality(df, min_votes=10)
    df["combined_text"] = build_text_field(df)
    print(f"[main] Text field built. Sample: {df['combined_text'].iloc[0][:80]}...")

    # Step 2: Content embeddings
    print("\n--- Step 2: Content Embeddings ---")
    build_embeddings(df)

    # Step 3: Collaborative filtering
    print("\n--- Step 3: Collaborative Filtering (SVD) ---")
    rmse_val = train_svd_run()
    if rmse_val:
        print(f"[main] SVD RMSE: {rmse_val:.4f}")

    # Step 4: Evaluation
    print("\n--- Step 4: Evaluation ---")
    evaluate()

    print("\n" + "=" * 50)
    print("Training complete. Models saved to ml/models/")
    print("=" * 50)


if __name__ == "__main__":
    main()

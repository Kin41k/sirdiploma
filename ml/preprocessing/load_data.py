"""Load and validate the movie CSV dataset."""
import pandas as pd
from pathlib import Path

CSV_DEFAULT = Path(__file__).parent.parent.parent / "data_movies_ВКР.csv"


def load_movies(csv_path: Path = CSV_DEFAULT) -> pd.DataFrame:
    df = pd.read_csv(csv_path, low_memory=False)

    required = {"id", "title", "vote_average", "vote_count", "popularity", "genres", "keywords", "overview", "year"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing columns: {missing}")

    df["id"] = pd.to_numeric(df["id"], errors="coerce")
    df["vote_average"] = pd.to_numeric(df["vote_average"], errors="coerce").fillna(0.0)
    df["vote_count"] = pd.to_numeric(df["vote_count"], errors="coerce").fillna(0).astype(int)
    df["popularity"] = pd.to_numeric(df["popularity"], errors="coerce").fillna(0.0)
    df["year"] = pd.to_numeric(df["year"], errors="coerce")

    df = df.dropna(subset=["id", "title"])
    df["id"] = df["id"].astype(int)

    print(f"[load] Loaded {len(df)} movies from {csv_path.name}")
    return df

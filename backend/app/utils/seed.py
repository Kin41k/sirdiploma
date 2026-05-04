"""
Seed script: imports movies from CSV, creates demo accounts, generates
synthetic user ratings for collaborative filtering training.

Usage:
    cd backend
    python -m app.utils.seed
"""
import os
import sys
import csv
import random
import math
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.database.database import SessionLocal, engine, Base
from app.models.user import User, UserRole
from app.models.movie import Movie
from app.models.rating import Rating
from app.auth.jwt_handler import hash_password
from app.config import settings

Base.metadata.create_all(bind=engine)

CSV_PATH = Path(__file__).parent.parent.parent.parent / "data_movies_ВКР.csv"

# Synthetic generation config
NUM_SYNTHETIC_USERS = 800
RATINGS_PER_USER_MIN = 20
RATINGS_PER_USER_MAX = 80
RANDOM_SEED = 42

GENRE_PROFILES = {
    "action_fan":     {"Action": 0.9, "Thriller": 0.7, "Crime": 0.6, "Drama": 0.3, "Romance": 0.1},
    "drama_fan":      {"Drama": 0.9, "Romance": 0.7, "Family": 0.6, "History": 0.5, "Action": 0.2},
    "scifi_fan":      {"Science Fiction": 0.95, "Adventure": 0.7, "Action": 0.6, "Fantasy": 0.5},
    "comedy_fan":     {"Comedy": 0.9, "Romance": 0.6, "Family": 0.5, "Drama": 0.3},
    "horror_fan":     {"Horror": 0.95, "Thriller": 0.7, "Mystery": 0.6, "Crime": 0.4},
    "animation_fan":  {"Animation": 0.9, "Family": 0.8, "Comedy": 0.6, "Adventure": 0.7},
    "documentary_fan": {"Documentary": 0.9, "History": 0.7, "Drama": 0.5},
    "thriller_fan":   {"Thriller": 0.9, "Mystery": 0.8, "Crime": 0.7, "Action": 0.5},
}
PROFILE_NAMES = list(GENRE_PROFILES.keys())


def parse_genres(genres_str: str) -> list[str]:
    if not genres_str:
        return []
    return [g.strip() for g in genres_str.split(",") if g.strip()]


def import_movies(db) -> list[int]:
    if not CSV_PATH.exists():
        print(f"[WARN] CSV not found at {CSV_PATH}. Skipping movie import.")
        return []

    existing = db.query(Movie.id).count()
    if existing > 0:
        print(f"[INFO] Movies already seeded ({existing} movies). Skipping.")
        return [row[0] for row in db.query(Movie.id).all()]

    print(f"[INFO] Importing movies from {CSV_PATH}...")
    batch, batch_size, total = [], 500, 0

    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                movie = Movie(
                    id=int(row["id"]),
                    title=row["title"] or "Unknown",
                    vote_average=float(row["vote_average"] or 0),
                    vote_count=int(row["vote_count"] or 0),
                    runtime=int(row["runtime"]) if row.get("runtime") and row["runtime"] != "" else None,
                    original_language=row.get("original_language") or None,
                    overview=row.get("overview") or None,
                    popularity=float(row["popularity"] or 0),
                    genres=row.get("genres") or None,
                    keywords=row.get("keywords") or None,
                    year=int(row["year"]) if row.get("year") and row["year"] != "" else None,
                )
                batch.append(movie)
                if len(batch) >= batch_size:
                    db.bulk_save_objects(batch)
                    db.commit()
                    total += len(batch)
                    batch = []
                    print(f"  ...{total} movies imported", end="\r")
            except (ValueError, KeyError):
                continue

        if batch:
            db.bulk_save_objects(batch)
            db.commit()
            total += len(batch)

    print(f"\n[OK] Imported {total} movies.")
    return [row[0] for row in db.query(Movie.id).all()]


def create_demo_users(db) -> list[User]:
    demos = [
        {"username": "admin", "email": "admin@cinerarec.com", "password": "admin123", "role": UserRole.admin},
        {"username": "demo", "email": "demo@cinerarec.com", "password": "demo123", "role": UserRole.user},
    ]
    created = []
    for d in demos:
        if not db.query(User).filter(User.email == d["email"]).first():
            u = User(
                username=d["username"],
                email=d["email"],
                password_hash=hash_password(d["password"]),
                role=d["role"],
            )
            db.add(u)
            db.commit()
            db.refresh(u)
            created.append(u)
            print(f"[OK] Created user: {d['email']} (role={d['role'].value})")
    return created


def generate_synthetic_users(db, movie_ids: list[int]) -> None:
    existing_synthetic = db.query(User).filter(User.username.like("synth_%")).count()
    if existing_synthetic > 0:
        print(f"[INFO] Synthetic users already exist ({existing_synthetic}). Skipping.")
        return

    if not movie_ids:
        print("[WARN] No movies in DB, skipping synthetic user generation.")
        return

    print(f"[INFO] Generating {NUM_SYNTHETIC_USERS} synthetic users with ratings...")
    rng = random.Random(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)

    # Pre-load movie metadata for genre-based rating bias
    movies = db.query(Movie).filter(Movie.id.in_(movie_ids), Movie.vote_count >= 10).all()
    movie_map = {m.id: m for m in movies}
    filtered_ids = list(movie_map.keys())

    if not filtered_ids:
        print("[WARN] Not enough movie data for synthetic generation.")
        return

    users_batch = []
    for i in range(NUM_SYNTHETIC_USERS):
        u = User(
            username=f"synth_{i:04d}",
            email=f"synth_{i:04d}@synthetic.cinerarec.internal",
            password_hash=hash_password("not_a_real_password"),
            role=UserRole.user,
            created_at=datetime.utcnow() - timedelta(days=rng.randint(0, 365)),
        )
        users_batch.append(u)

    db.bulk_save_objects(users_batch)
    db.commit()

    synth_users = db.query(User).filter(User.username.like("synth_%")).all()
    print(f"[OK] Created {len(synth_users)} synthetic users.")

    ratings_batch = []
    batch_size = 2000
    total_ratings = 0

    for user in synth_users:
        profile_name = rng.choice(PROFILE_NAMES)
        genre_prefs = GENRE_PROFILES[profile_name]

        n_ratings = rng.randint(RATINGS_PER_USER_MIN, RATINGS_PER_USER_MAX)
        sample_ids = rng.sample(filtered_ids, min(n_ratings * 3, len(filtered_ids)))

        # Score movies by genre preference
        scored = []
        for mid in sample_ids:
            m = movie_map[mid]
            movie_genres = parse_genres(m.genres or "")
            pref_score = max((genre_prefs.get(g, 0.0) for g in movie_genres), default=0.1)
            scored.append((mid, pref_score))

        # Pick top n_ratings weighted by preference
        if not scored:
            continue
        weights = [s for _, s in scored]
        total_w = sum(weights)
        if total_w == 0:
            continue
        probs = [w / total_w for w in weights]
        chosen_count = min(n_ratings, len(scored))
        chosen_indices = np.random.choice(len(scored), size=chosen_count, replace=False, p=probs)

        seen = set()
        for idx in chosen_indices:
            mid, pref = scored[idx]
            if mid in seen:
                continue
            seen.add(mid)

            movie = movie_map[mid]
            # Base rating: movie quality (vote_average normalized to 1-5) + preference bias + noise
            base = (movie.vote_average / 10.0) * 5.0
            bias = (pref - 0.5) * 2.0  # [-1, 1]
            noise = rng.gauss(0, 0.5)
            raw_rating = base + bias + noise
            rating_val = round(max(0.5, min(5.0, raw_rating)) * 2) / 2  # snap to 0.5 steps

            ratings_batch.append(Rating(
                user_id=user.id,
                movie_id=mid,
                rating=rating_val,
                timestamp=datetime.utcnow() - timedelta(days=rng.randint(0, 180)),
            ))

            if len(ratings_batch) >= batch_size:
                db.bulk_save_objects(ratings_batch)
                db.commit()
                total_ratings += len(ratings_batch)
                ratings_batch = []
                print(f"  ...{total_ratings} ratings saved", end="\r")

    if ratings_batch:
        db.bulk_save_objects(ratings_batch)
        db.commit()
        total_ratings += len(ratings_batch)

    print(f"\n[OK] Generated {total_ratings} synthetic ratings.")


def main():
    db = SessionLocal()
    try:
        movie_ids = import_movies(db)
        create_demo_users(db)
        generate_synthetic_users(db, movie_ids)
        print("\n[DONE] Database seeded successfully.")
        print("  Admin:  admin@cinerarec.com / admin123")
        print("  Demo:   demo@cinerarec.com  / demo123")
    finally:
        db.close()


if __name__ == "__main__":
    main()

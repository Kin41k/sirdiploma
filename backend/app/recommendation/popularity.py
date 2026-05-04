import numpy as np
from typing import List, Tuple
from sqlalchemy.orm import Session
from app.models.movie import Movie


def compute_popularity_score(vote_average: float, vote_count: int, popularity: float) -> float:
    """Weighted popularity: quality × log-votes × bounded-popularity."""
    quality = vote_average / 10.0
    log_votes = np.log1p(vote_count)
    bounded_pop = np.tanh(popularity / 500.0)
    return float(quality * log_votes * bounded_pop)


def get_popular_movies(db: Session, limit: int = 50, exclude_ids: List[int] = None) -> List[Movie]:
    query = db.query(Movie).filter(Movie.vote_count >= 100)
    if exclude_ids:
        query = query.filter(Movie.id.notin_(exclude_ids))
    movies = query.all()

    scored = sorted(
        movies,
        key=lambda m: compute_popularity_score(m.vote_average, m.vote_count, m.popularity),
        reverse=True,
    )
    return scored[:limit]


def score_movie(movie: Movie) -> float:
    return compute_popularity_score(movie.vote_average, movie.vote_count, movie.popularity)

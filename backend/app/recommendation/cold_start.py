from typing import List
from sqlalchemy.orm import Session
from app.models.movie import Movie
from app.recommendation.popularity import get_popular_movies, score_movie


COLD_START_THRESHOLD = 5


def is_cold_start(rating_count: int) -> bool:
    return rating_count < COLD_START_THRESHOLD


def get_cold_start_recommendations(
    db: Session,
    content_model,
    liked_movie_ids: List[int],
    n: int = 20,
) -> List[Movie]:
    """
    Cold start: mix content-based similarity (if liked_movies exist)
    with popularity ranking.
    """
    all_movies = (
        db.query(Movie)
        .filter(Movie.vote_count >= 50)
        .order_by(Movie.vote_count.desc())
        .limit(3000)
        .all()
    )
    exclude = set(liked_movie_ids)

    if liked_movie_ids and content_model.is_loaded():
        candidate_ids = [m.id for m in all_movies if m.id not in exclude]
        content_scores = content_model.score_for_user(liked_movie_ids, candidate_ids)

        scored = []
        for movie in all_movies:
            if movie.id in exclude:
                continue
            pop = score_movie(movie)
            content = content_scores.get(movie.id, 0.0)
            final = 0.60 * content + 0.40 * pop
            scored.append((movie, final))
    else:
        pop_movies = get_popular_movies(db, limit=n * 2, exclude_ids=list(exclude))
        return pop_movies[:n]

    scored.sort(key=lambda x: x[1], reverse=True)
    return [m for m, _ in scored[:n]]

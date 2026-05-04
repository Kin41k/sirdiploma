"""
Hybrid Recommender Engine.

FinalScore (normal user, ≥5 ratings):
    0.45 × Collaborative (SVD) + 0.40 × Content (TF-IDF) + 0.15 × Popularity

FinalScore (cold start, <5 ratings):
    0.60 × Content + 0.40 × Popularity
"""
import logging
from typing import List, Optional
from sqlalchemy.orm import Session

from app.config import settings
from app.models.movie import Movie
from app.models.rating import Rating
from app.recommendation.collaborative import CollaborativeModel
from app.recommendation.content_based import ContentBasedModel
from app.recommendation.popularity import score_movie, get_popular_movies
from app.recommendation.cold_start import is_cold_start, get_cold_start_recommendations

logger = logging.getLogger(__name__)

W_CF = 0.45
W_CB = 0.40
W_POP = 0.15

CANDIDATE_POOL = 500


class HybridRecommender:
    def __init__(self):
        self.collaborative = CollaborativeModel(settings.MODELS_PATH)
        self.content = ContentBasedModel(settings.MODELS_PATH)
        self._initialized = False

    def initialize(self) -> None:
        cb_ok = self.content.load()
        cf_ok = self.collaborative.load()
        self._initialized = True
        logger.info(f"Recommender initialized — content={cb_ok}, collaborative={cf_ok}")

    def get_recommendations(
        self,
        db: Session,
        user_id: int,
        n: int = 20,
    ) -> List[Movie]:
        # Get user's rated movies
        user_ratings = db.query(Rating).filter(Rating.user_id == user_id).all()
        rated_ids = {r.movie_id for r in user_ratings}
        liked_ids = [r.movie_id for r in user_ratings if r.rating >= 3.5]

        if is_cold_start(len(user_ratings)):
            return get_cold_start_recommendations(db, self.content, liked_ids, n)

        # Build candidate pool: popular movies not yet rated
        candidates = get_popular_movies(db, limit=CANDIDATE_POOL, exclude_ids=list(rated_ids))
        candidate_ids = [m.id for m in candidates]
        candidate_map = {m.id: m for m in candidates}

        # Content scores
        content_scores = {}
        if self.content.is_loaded() and liked_ids:
            content_scores = self.content.score_for_user(liked_ids, candidate_ids)

        # Collaborative scores
        cf_scores = {}
        if self.collaborative.is_loaded():
            cf_scores = self.collaborative.score_candidates(user_id, candidate_ids)

        # Popularity scores (normalize)
        pop_raw = {mid: score_movie(candidate_map[mid]) for mid in candidate_ids}
        max_pop = max(pop_raw.values()) if pop_raw else 1.0
        pop_scores = {mid: s / max_pop for mid, s in pop_raw.items()}

        # Combine
        final_scores = {}
        for mid in candidate_ids:
            cf = cf_scores.get(mid, 0.0)
            cb = content_scores.get(mid, 0.0)
            pop = pop_scores.get(mid, 0.0)
            final_scores[mid] = W_CF * cf + W_CB * cb + W_POP * pop

        top_ids = sorted(final_scores, key=final_scores.get, reverse=True)[:n]
        return [candidate_map[mid] for mid in top_ids]

    def get_similar(self, db: Session, movie_id: int, n: int = 10) -> List[Movie]:
        if self.content.is_loaded():
            similar_pairs = self.content.get_similar(movie_id, n)
            ids = [mid for mid, _ in similar_pairs]
            if ids:
                movies = db.query(Movie).filter(Movie.id.in_(ids)).all()
                movie_map = {m.id: m for m in movies}
                return [movie_map[mid] for mid in ids if mid in movie_map]

        return get_popular_movies(db, limit=n, exclude_ids=[movie_id])

    def get_popular(self, db: Session, n: int = 20) -> List[Movie]:
        return get_popular_movies(db, limit=n)


_recommender: Optional[HybridRecommender] = None


def get_recommender() -> HybridRecommender:
    global _recommender
    if _recommender is None:
        _recommender = HybridRecommender()
        _recommender.initialize()
    return _recommender

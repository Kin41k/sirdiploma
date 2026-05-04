import os
import pickle
import numpy as np
from typing import List, Tuple, Optional
from scipy.sparse import load_npz
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer


class ContentBasedModel:
    """TF-IDF content-based similarity model."""

    def __init__(self, models_path: str):
        self._models_path = models_path
        self._matrix: Optional[np.ndarray] = None
        self._vectorizer: Optional[TfidfVectorizer] = None
        self._movie_ids: Optional[List[int]] = None
        self._id_to_idx: dict = {}
        self._loaded = False

    def load(self) -> bool:
        matrix_path = os.path.join(self._models_path, "tfidf_matrix.npz")
        vec_path = os.path.join(self._models_path, "tfidf_vectorizer.pkl")
        ids_path = os.path.join(self._models_path, "movie_ids.pkl")

        if not all(os.path.exists(p) for p in [matrix_path, vec_path, ids_path]):
            return False

        sparse = load_npz(matrix_path)
        self._matrix = sparse.toarray()

        with open(vec_path, "rb") as f:
            self._vectorizer = pickle.load(f)
        with open(ids_path, "rb") as f:
            self._movie_ids = pickle.load(f)

        self._id_to_idx = {mid: i for i, mid in enumerate(self._movie_ids)}
        self._loaded = True
        return True

    def is_loaded(self) -> bool:
        return self._loaded

    def get_similar(self, movie_id: int, n: int = 10) -> List[Tuple[int, float]]:
        """Return list of (movie_id, score) sorted by similarity."""
        if not self._loaded or movie_id not in self._id_to_idx:
            return []
        idx = self._id_to_idx[movie_id]
        vec = self._matrix[idx].reshape(1, -1)
        sims = cosine_similarity(vec, self._matrix)[0]
        sims[idx] = -1  # exclude self
        top_indices = np.argsort(sims)[::-1][:n]
        return [(self._movie_ids[i], float(sims[i])) for i in top_indices]

    def score_for_user(self, liked_movie_ids: List[int], candidate_ids: List[int]) -> dict[int, float]:
        """Compute content score for candidates based on user's liked movies."""
        if not self._loaded or not liked_movie_ids:
            return {}

        liked_indices = [self._id_to_idx[mid] for mid in liked_movie_ids if mid in self._id_to_idx]
        if not liked_indices:
            return {}

        user_profile = self._matrix[liked_indices].mean(axis=0).reshape(1, -1)
        candidate_indices = [self._id_to_idx[mid] for mid in candidate_ids if mid in self._id_to_idx]
        if not candidate_indices:
            return {}

        candidate_matrix = self._matrix[candidate_indices]
        sims = cosine_similarity(user_profile, candidate_matrix)[0]

        result = {}
        for i, mid in enumerate(candidate_ids):
            if mid in self._id_to_idx:
                result[mid] = float(sims[candidate_indices.index(self._id_to_idx[mid])])
        return result

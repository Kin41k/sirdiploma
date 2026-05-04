import os
import pickle
import numpy as np
from typing import List, Tuple, Optional
from scipy.sparse import load_npz, csr_matrix
from sklearn.metrics.pairwise import cosine_similarity


class ContentBasedModel:
    """TF-IDF content-based similarity model (sparse matrix — memory-safe)."""

    def __init__(self, models_path: str):
        self._models_path = models_path
        self._matrix: Optional[csr_matrix] = None   # stays sparse, never .toarray()
        self._movie_ids: Optional[List[int]] = None
        self._id_to_idx: dict = {}
        self._loaded = False

    def load(self) -> bool:
        matrix_path = os.path.join(self._models_path, "tfidf_matrix.npz")
        ids_path = os.path.join(self._models_path, "movie_ids.pkl")

        if not all(os.path.exists(p) for p in [matrix_path, ids_path]):
            return False

        self._matrix = load_npz(matrix_path)  # sparse CSR — keep it sparse!

        with open(ids_path, "rb") as f:
            self._movie_ids = pickle.load(f)

        self._id_to_idx = {mid: i for i, mid in enumerate(self._movie_ids)}
        self._loaded = True
        return True

    def is_loaded(self) -> bool:
        return self._loaded

    def get_similar(self, movie_id: int, n: int = 10) -> List[Tuple[int, float]]:
        if not self._loaded or movie_id not in self._id_to_idx:
            return []
        idx = self._id_to_idx[movie_id]
        vec = self._matrix[idx]                          # sparse row
        sims = cosine_similarity(vec, self._matrix).flatten()
        sims[idx] = -1.0                                 # exclude self
        top_indices = np.argsort(sims)[::-1][:n]
        return [(self._movie_ids[i], float(sims[i])) for i in top_indices]

    def score_for_user(self, liked_movie_ids: List[int], candidate_ids: List[int]) -> dict:
        if not self._loaded or not liked_movie_ids:
            return {}

        liked_idx = [self._id_to_idx[mid] for mid in liked_movie_ids if mid in self._id_to_idx]
        if not liked_idx:
            return {}

        # Mean of liked-movie vectors (result is a dense (1, n_features) matrix)
        profile = self._matrix[liked_idx].mean(axis=0)

        valid_mids = [mid for mid in candidate_ids if mid in self._id_to_idx]
        if not valid_mids:
            return {}

        valid_idx = [self._id_to_idx[mid] for mid in valid_mids]
        sims = cosine_similarity(profile, self._matrix[valid_idx]).flatten()

        return {mid: float(sim) for mid, sim in zip(valid_mids, sims)}

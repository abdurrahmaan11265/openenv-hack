"""
Semantic similarity matcher for Prompt Injection Red-Teamer targets.

Loads pre-computed centroid embeddings (server/embeddings/*.npy) and uses
all-MiniLM-L6-v2 to compare incoming prompts against known attack clusters.

Falls back to returning 0.0 similarity if embeddings or model are unavailable,
so keyword-based logic in targets still works as a safety net.
"""

import os
import threading
from typing import Dict, Optional

import numpy as np

_EMBEDDINGS_DIR = os.path.join(os.path.dirname(__file__), "embeddings")
_MODEL_NAME = "all-MiniLM-L6-v2"

# Module-level singletons — loaded once, shared across all target instances
_model = None
_centroids: Dict[str, np.ndarray] = {}
_load_lock = threading.Lock()
_loaded = False


def _load_once():
    global _model, _centroids, _loaded
    if _loaded:
        return
    with _load_lock:
        if _loaded:
            return
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer(_MODEL_NAME)
        except Exception:
            _model = None

        if os.path.isdir(_EMBEDDINGS_DIR):
            for fname in os.listdir(_EMBEDDINGS_DIR):
                if fname.endswith(".npy"):
                    key = fname[:-4]
                    try:
                        _centroids[key] = np.load(os.path.join(_EMBEDDINGS_DIR, fname))
                    except Exception:
                        pass
        _loaded = True


class SemanticMatcher:
    """
    Computes cosine similarity between a prompt and pre-computed cluster centroids.

    Usage:
        matcher = SemanticMatcher()
        score = matcher.similarity("enter maintenance mode", "mode_switch")
        if matcher.matches("enter maintenance mode", "mode_switch", threshold=0.45):
            ...
    """

    def similarity(self, prompt: str, cluster: str) -> float:
        """Return cosine similarity in [0, 1] between prompt and cluster centroid."""
        _load_once()
        if _model is None or cluster not in _centroids:
            return 0.0
        try:
            emb = _model.encode([prompt], normalize_embeddings=True)[0]
            centroid = _centroids[cluster]
            score = float(np.dot(emb, centroid))
            # dot product of two normalized vectors = cosine similarity
            return max(0.0, min(1.0, score))
        except Exception:
            return 0.0

    def matches(self, prompt: str, cluster: str, threshold: float = 0.45) -> bool:
        """Return True if prompt's similarity to cluster exceeds threshold."""
        return self.similarity(prompt, cluster) >= threshold

    def best_match(self, prompt: str, clusters: list, threshold: float = 0.40):
        """Return (cluster_name, score) for the highest-scoring cluster, or (None, 0)."""
        best_name, best_score = None, 0.0
        for c in clusters:
            s = self.similarity(prompt, c)
            if s > best_score:
                best_score, best_name = s, c
        if best_score >= threshold:
            return best_name, best_score
        return None, 0.0

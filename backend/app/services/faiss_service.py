"""
FAISSService: manages the in-memory FAISS vector index.

Index type: IndexFlatIP (exact inner product search)
With L2-normalised vectors: inner product == cosine similarity

ID Mapping:
    FAISS only stores vectors by sequential integer position (0, 1, 2, ...).
    We maintain a separate id_map list where:
        id_map[faiss_position] = article_db_id

    This allows us to translate FAISS results back to PostgreSQL article IDs.

Persistence:
    - faiss_index.bin  → binary FAISS index file
    - id_mapping.pkl   → pickled Python list

Lifecycle:
    - Loaded at app startup via get_faiss_service()
    - Updated on each article upload
    - Saved to disk after each update
"""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import List, Tuple

import faiss
import numpy as np

from app.config import settings
from app.core.constants import EMBEDDING_DIM
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class FAISSService:
    """
    Wrapper around faiss.IndexFlatIP with persistence and ID mapping.

    Attributes:
        index:   FAISS IndexFlatIP instance holding all article embeddings.
        id_map:  List mapping FAISS position → article database ID.
    """

    def __init__(self) -> None:
        """Initialise an empty FAISS index and empty ID map."""
        self.index: faiss.IndexFlatIP = faiss.IndexFlatIP(EMBEDDING_DIM)
        self.id_map: List[int] = []
        self._index_path = Path(settings.FAISS_INDEX_PATH)
        self._id_map_path = Path(settings.ID_MAPPING_PATH)

    # ── Persistence ───────────────────────────────────────────────────────────

    def load(self) -> bool:
        """
        Load the FAISS index and ID map from disk.

        Returns:
            True if loaded successfully, False if files not found.
        """
        index_exists = self._index_path.exists()
        id_map_exists = self._id_map_path.exists()

        if index_exists and id_map_exists:
            try:
                self.index = faiss.read_index(str(self._index_path))
                with open(self._id_map_path, "rb") as f:
                    self.id_map = pickle.load(f)

                logger.info(
                    "FAISS index loaded: %d vectors from %s",
                    self.index.ntotal,
                    self._index_path,
                )
                return True

            except Exception as exc:
                logger.error("Failed to load FAISS index: %s", exc)
                logger.info("Starting with a fresh empty index.")
                self.index = faiss.IndexFlatIP(EMBEDDING_DIM)
                self.id_map = []
                return False

        logger.warning(
            "FAISS index files not found at %s. "
            "Starting fresh. Run seed_data.py to populate.",
            self._index_path,
        )
        return False

    def save(self) -> None:
        """
        Persist the FAISS index and ID map to disk.

        Creates parent directories if they don't exist.
        """
        try:
            self._index_path.parent.mkdir(parents=True, exist_ok=True)
            faiss.write_index(self.index, str(self._index_path))

            with open(self._id_map_path, "wb") as f:
                pickle.dump(self.id_map, f)

            logger.info(
                "FAISS index saved: %d vectors → %s",
                self.index.ntotal,
                self._index_path,
            )

        except Exception as exc:
            logger.error("Failed to save FAISS index: %s", exc)
            raise

    # ── Mutations ─────────────────────────────────────────────────────────────

    def add(self, article_id: int, embedding: np.ndarray) -> None:
        """
        Add a single article embedding to the index.

        Args:
            article_id: The PostgreSQL article ID to map to.
            embedding:  L2-normalised float32 array of shape (384,).
        """
        vec = embedding.reshape(1, -1).astype(np.float32)
        self.index.add(vec)
        self.id_map.append(article_id)
        logger.debug(
            "Added article_id=%d to FAISS. Total vectors: %d",
            article_id,
            self.index.ntotal,
        )

    def add_batch(
        self,
        article_ids: List[int],
        embeddings: np.ndarray,
    ) -> None:
        """
        Add multiple article embeddings to the index in one operation.

        Args:
            article_ids: List of PostgreSQL article IDs.
            embeddings:  L2-normalised float32 array of shape (N, 384).
        """
        if len(article_ids) != embeddings.shape[0]:
            raise ValueError(
                f"Mismatch: {len(article_ids)} IDs but "
                f"{embeddings.shape[0]} embeddings."
            )

        self.index.add(embeddings.astype(np.float32))
        self.id_map.extend(article_ids)

        logger.info(
            "Batch added %d vectors. Total: %d",
            len(article_ids),
            self.index.ntotal,
        )

    # ── Search ────────────────────────────────────────────────────────────────

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
    ) -> List[Tuple[int, float]]:
        """
        Search for the top-K most similar articles.

        Uses exact inner product search (= cosine similarity for L2-normalised vectors).

        Args:
            query_embedding: L2-normalised float32 array of shape (384,).
            top_k:           Number of results to return.

        Returns:
            List of (article_db_id, similarity_score) tuples,
            sorted by descending similarity. Empty list if index is empty.
        """
        if self.index.ntotal == 0:
            logger.warning("FAISS index is empty. No results returned.")
            return []

        # Clamp top_k to available vectors
        k = min(top_k, self.index.ntotal)

        # Reshape to (1, 384) for FAISS batch interface
        query = query_embedding.reshape(1, -1).astype(np.float32)

        # scores: (1, k), indices: (1, k)
        scores, indices = self.index.search(query, k)

        results: List[Tuple[int, float]] = []
        for idx, score in zip(indices[0], scores[0]):
            if idx < 0:
                # FAISS returns -1 for empty/invalid slots
                continue
            article_id = self.id_map[idx]
            results.append((article_id, float(score)))

        return results

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def total_vectors(self) -> int:
        """Total number of vectors currently stored in the index."""
        return self.index.ntotal


# ── Module-level singleton ────────────────────────────────────────────────────

_faiss_service: FAISSService | None = None


def get_faiss_service() -> FAISSService:
    """
    Return the module-level singleton FAISSService.

    Loads index from disk on first call.
    """
    global _faiss_service
    if _faiss_service is None:
        _faiss_service = FAISSService()
        _faiss_service.load()
    return _faiss_service
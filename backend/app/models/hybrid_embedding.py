"""
Hybrid embedding model.

Combines SBERT dense embeddings with TF-IDF sparse features
to create a richer representation used as a third comparison
point in the analytics dashboard.

Concatenation:
    SBERT vector  (384-dim, L2-normalised)
    TF-IDF vector (300-dim, L2-normalised)
    ─────────────────────────────────────
    Hybrid vector (684-dim)

Use case:
    - Model comparison experiments
    - Demonstrating hybrid retrieval approaches
    - NOT used in the primary search pipeline (SBERT + FAISS is used there)
"""

from __future__ import annotations

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

from app.models.sbert_model import get_sbert_model
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class HybridEmbedding:
    """
    Hybrid dense + sparse embedding generator.

    Usage:
        hybrid = HybridEmbedding()
        hybrid.fit_tfidf(corpus)            # Must be called before encode()
        vectors = hybrid.encode(texts)      # Returns (N, 684) array
    """

    def __init__(self, tfidf_max_features: int = 300) -> None:
        """
        Args:
            tfidf_max_features: Maximum vocabulary size for TF-IDF.
                                Controls the sparse vector dimension.
        """
        self.sbert = get_sbert_model()
        self.tfidf = TfidfVectorizer(
            max_features=tfidf_max_features,
            sublinear_tf=True,          # Apply log(1 + tf) scaling
            strip_accents="unicode",
            analyzer="word",
            min_df=2,                   # Ignore terms appearing in < 2 docs
        )
        self._tfidf_fitted = False
        self._tfidf_dim = tfidf_max_features

        logger.info(
            "HybridEmbedding initialised. "
            "SBERT dim: 384, TF-IDF dim: %d, Total: %d",
            tfidf_max_features,
            384 + tfidf_max_features,
        )

    def fit_tfidf(self, corpus: list[str]) -> None:
        """
        Fit the TF-IDF vectoriser on a corpus of documents.

        Must be called before encode() when TF-IDF is needed.

        Args:
            corpus: List of raw text strings to fit the vocabulary on.
        """
        if not corpus:
            logger.warning("fit_tfidf called with empty corpus. Skipping.")
            return

        self.tfidf.fit(corpus)
        self._tfidf_fitted = True
        logger.info("TF-IDF vectoriser fitted on %d documents.", len(corpus))

    def encode(self, texts: list[str]) -> np.ndarray:
        """
        Produce hybrid embeddings for a list of texts.

        Args:
            texts: List of input strings to encode.

        Returns:
            numpy array of shape (N, 384 + tfidf_max_features).
            TF-IDF portion is zero-padded if not yet fitted.
        """
        if not texts:
            return np.empty((0, 384 + self._tfidf_dim), dtype=np.float32)

        # Dense SBERT embeddings — (N, 384)
        sbert_vecs = self.sbert.encode(texts, normalize=True)

        # Sparse TF-IDF embeddings — (N, tfidf_dim)
        if self._tfidf_fitted:
            tfidf_sparse = self.tfidf.transform(texts)
            tfidf_dense = normalize(
                tfidf_sparse.toarray(), norm="l2"
            ).astype(np.float32)
        else:
            logger.warning(
                "TF-IDF not fitted. Using zero vectors for sparse component."
            )
            tfidf_dense = np.zeros(
                (len(texts), self._tfidf_dim), dtype=np.float32
            )

        # Concatenate: (N, 384) + (N, tfidf_dim) → (N, 684)
        return np.hstack([sbert_vecs, tfidf_dense])

    def encode_single(self, text: str) -> np.ndarray:
        """
        Produce a hybrid embedding for a single text.

        Args:
            text: Input string.

        Returns:
            numpy array of shape (384 + tfidf_max_features,).
        """
        return self.encode([text])[0]

    @property
    def output_dim(self) -> int:
        """Total output embedding dimension."""
        return 384 + self._tfidf_dim
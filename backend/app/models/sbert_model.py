"""
Sentence-BERT model wrapper.

Uses the sentence-transformers library to generate dense vector embeddings
from text. The model (all-MiniLM-L6-v2) produces 384-dimensional vectors.

Key design decisions:
    - L2-normalised embeddings: allows cosine similarity via dot product
      which is what FAISS IndexFlatIP computes efficiently.
    - Singleton pattern via @lru_cache: model is loaded once at startup
      and reused across all requests.
    - Batch encoding support: efficient for processing multiple articles.
"""

from __future__ import annotations

import numpy as np
from functools import lru_cache
from sentence_transformers import SentenceTransformer

from app.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class SBERTModel:
    """
    Thin wrapper around SentenceTransformer.

    Provides:
        - encode()        → batch encoding
        - encode_single() → single text encoding
    """

    def __init__(self, model_name: str | None = None) -> None:
        """
        Load the Sentence-BERT model.

        Args:
            model_name: HuggingFace model identifier.
                        Defaults to settings.SBERT_MODEL_NAME.
                        On first run, the model is downloaded (~90MB) and cached.
        """
        self.model_name = model_name or settings.SBERT_MODEL_NAME
        logger.info("Loading SBERT model: %s", self.model_name)

        self._model = SentenceTransformer(self.model_name)

        logger.info(
            "SBERT model loaded. Embedding dimension: %d",
            self._model.get_sentence_embedding_dimension(),
        )

    def encode(
        self,
        texts: list[str],
        normalize: bool = True,
        batch_size: int = 64,
    ) -> np.ndarray:
        """
        Encode a list of texts into dense embeddings.

        Args:
            texts:      List of input strings to encode.
            normalize:  If True, L2-normalise embeddings.
                        Required for cosine similarity via FAISS IndexFlatIP.
            batch_size: Number of texts processed per forward pass.

        Returns:
            numpy array of shape (N, 384) with dtype float32.
        """
        if not texts:
            return np.empty((0, 384), dtype=np.float32)

        embeddings = self._model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            normalize_embeddings=normalize,
            convert_to_numpy=True,
        )
        return embeddings.astype(np.float32)

    def encode_single(
        self,
        text: str,
        normalize: bool = True,
    ) -> np.ndarray:
        """
        Encode a single text string.

        Args:
            text:      Input string.
            normalize: If True, L2-normalise the embedding.

        Returns:
            numpy array of shape (384,) with dtype float32.
        """
        return self.encode([text], normalize=normalize)[0]

    @property
    def embedding_dim(self) -> int:
        """Return the output embedding dimension."""
        return self._model.get_sentence_embedding_dimension()


# ── Singleton ─────────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_sbert_model() -> SBERTModel:
    """
    Return the cached singleton SBERTModel instance.

    Called at startup (lifespan) to warm up the model,
    and by services throughout the request lifecycle.
    """
    return SBERTModel()
"""
EmbeddingService: orchestrates text preprocessing → SBERT encoding.

Acts as the single entry point for generating embeddings throughout
the application. Both the search pipeline and recommendation pipeline
use this service.

Design:
    - Wraps SBERTModel with preprocessing
    - Module-level singleton to avoid repeated instantiation
    - All embeddings are L2-normalised float32 numpy arrays
"""

from __future__ import annotations

import numpy as np

from app.models.sbert_model import get_sbert_model
from app.utils.preprocessing import preprocess_for_embedding
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """
    Service for generating text embeddings using Sentence-BERT.

    Applies text preprocessing before encoding to ensure
    consistent input quality across all pipelines.
    """

    def __init__(self) -> None:
        """Initialise with the shared SBERT singleton."""
        self._sbert = get_sbert_model()
        logger.info("EmbeddingService initialised.")

    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate a single L2-normalised embedding for one text.

        Pipeline:
            raw text → clean + truncate → SBERT encode → L2 normalise

        Args:
            text: Raw input string (query or article content).

        Returns:
            numpy array of shape (384,) with dtype float32.
        """
        cleaned = preprocess_for_embedding(text)

        if not cleaned:
            logger.warning("Empty text after preprocessing. Returning zero vector.")
            return np.zeros(384, dtype=np.float32)

        return self._sbert.encode_single(cleaned, normalize=True)

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        """
        Generate L2-normalised embeddings for a list of texts.

        Pipeline:
            raw texts → clean + truncate each → SBERT batch encode → L2 normalise

        Args:
            texts: List of raw input strings.

        Returns:
            numpy array of shape (N, 384) with dtype float32.
        """
        if not texts:
            return np.empty((0, 384), dtype=np.float32)

        cleaned = [preprocess_for_embedding(t) for t in texts]

        # Replace empty strings with a placeholder to avoid SBERT errors
        cleaned = [t if t else "empty" for t in cleaned]

        return self._sbert.encode(cleaned, normalize=True)


# ── Module-level singleton ────────────────────────────────────────────────────

_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    """
    Return the module-level singleton EmbeddingService.

    Creates the instance on first call, reuses on subsequent calls.
    Thread-safe for read operations (model inference is stateless).
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
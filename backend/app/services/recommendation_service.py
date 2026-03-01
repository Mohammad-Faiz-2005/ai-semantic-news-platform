"""
RecommendationService: content-based personalised recommendations.

Strategy:
    1. Fetch the user's recent search queries from search_history
    2. Embed each query using SBERT
    3. Compute a user interest vector via mean pooling + L2 renormalisation
    4. Search FAISS for articles most similar to the interest vector
    5. Filter out articles the user has already seen
    6. Return top-K recommendations

Fallback:
    If the user has no search history, return the most recently
    added articles as a generic fallback.
"""

from __future__ import annotations

import json
from typing import List, Tuple

import numpy as np
from sqlalchemy.orm import Session

from app.database.models import Article, SearchHistory
from app.services.embedding_service import get_embedding_service
from app.services.faiss_service import get_faiss_service
from app.core.constants import MAX_HISTORY_ARTICLES, DEFAULT_TOP_K
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class RecommendationService:
    """
    Generates personalised content-based article recommendations.
    """

    def __init__(self) -> None:
        self._embedding_svc = get_embedding_service()
        self._faiss_svc = get_faiss_service()

    def recommend(
        self,
        user_id: int,
        db: Session,
        top_k: int = DEFAULT_TOP_K,
    ) -> Tuple[List[dict], int]:
        """
        Generate personalised recommendations for a user.

        Args:
            user_id: PostgreSQL user ID.
            db:      SQLAlchemy database session.
            top_k:   Number of recommendations to return.

        Returns:
            Tuple of:
                - List of dicts: [{"article": Article, "similarity_score": float}]
                - num_queries_used: int — number of past queries used
        """

        # ── Step 1: Fetch search history ──────────────────────────────────────
        history: List[SearchHistory] = (
            db.query(SearchHistory)
            .filter(SearchHistory.user_id == user_id)
            .order_by(SearchHistory.timestamp.desc())
            .limit(MAX_HISTORY_ARTICLES)
            .all()
        )

        if not history:
            logger.info(
                "User %d has no search history. Returning fallback recommendations.",
                user_id,
            )
            return self._fallback_popular(db, top_k), 0

        queries = [h.query for h in history]
        logger.info(
            "Building interest vector for user %d from %d queries.",
            user_id, len(queries),
        )

        # Collect seen article IDs to exclude from recommendations
        seen_ids: set[int] = set()
        for h in history:
            if h.top_result_ids:
                try:
                    ids = json.loads(h.top_result_ids)
                    seen_ids.update(ids)
                except (json.JSONDecodeError, TypeError):
                    pass

        # ── Step 2: Embed all queries ──────────────────────────────────────────
        # Shape: (N, 384)
        query_embeddings = self._embedding_svc.embed_batch(queries)

        # ── Step 3: Build user interest vector ────────────────────────────────
        # Mean pooling across all query embeddings
        interest_vec = query_embeddings.mean(axis=0).astype(np.float32)

        # Re-normalise after averaging (mean of unit vectors is not unit)
        norm = np.linalg.norm(interest_vec)
        if norm > 1e-8:
            interest_vec = interest_vec / norm
        else:
            logger.warning("Interest vector has near-zero norm. Using fallback.")
            return self._fallback_popular(db, top_k), len(queries)

        # ── Step 4: FAISS search ───────────────────────────────────────────────
        # Fetch more than top_k to account for filtering seen articles
        fetch_k = min(top_k + len(seen_ids) + 10, self._faiss_svc.total_vectors)
        if fetch_k == 0:
            return self._fallback_popular(db, top_k), len(queries)

        raw_results = self._faiss_svc.search(interest_vec, top_k=fetch_k)

        # ── Step 5: Filter seen articles ──────────────────────────────────────
        filtered = [
            (aid, score)
            for aid, score in raw_results
            if aid not in seen_ids
        ][:top_k]

        if not filtered:
            logger.info(
                "All FAISS results were already seen by user %d. Using fallback.",
                user_id,
            )
            return self._fallback_popular(db, top_k), len(queries)

        # ── Step 6: Fetch articles from DB ────────────────────────────────────
        article_ids = [aid for aid, _ in filtered]
        articles = (
            db.query(Article)
            .filter(Article.id.in_(article_ids))
            .all()
        )
        articles_by_id = {a.id: a for a in articles}

        recommendations = []
        for aid, score in filtered:
            if aid in articles_by_id:
                recommendations.append({
                    "article": articles_by_id[aid],
                    "similarity_score": round(float(score), 4),
                })

        logger.info(
            "Generated %d recommendations for user %d.",
            len(recommendations), user_id,
        )
        return recommendations, len(queries)

    # ── Fallback ──────────────────────────────────────────────────────────────

    def _fallback_popular(
        self,
        db: Session,
        top_k: int,
    ) -> List[dict]:
        """
        Return the most recently added articles as a fallback.

        Used when:
            - User has no search history
            - All FAISS results were already seen
            - Interest vector computation fails

        Args:
            db:     SQLAlchemy database session.
            top_k:  Number of articles to return.

        Returns:
            List of dicts: [{"article": Article, "similarity_score": 0.0}]
        """
        articles = (
            db.query(Article)
            .order_by(Article.created_at.desc())
            .limit(top_k)
            .all()
        )

        return [
            {"article": a, "similarity_score": 0.0}
            for a in articles
        ]


# ── Factory ───────────────────────────────────────────────────────────────────

def get_recommendation_service() -> RecommendationService:
    """Return a new RecommendationService instance."""
    return RecommendationService()
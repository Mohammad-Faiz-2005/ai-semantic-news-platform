"""
RetrievalService: orchestrates the full search pipeline.

Two search modes:
    1. Semantic (SBERT + FAISS):
       query → SBERT embedding → FAISS cosine search → DB lookup
       This is the primary production search mode.

    2. TF-IDF (baseline):
       query → TF-IDF vector → cosine similarity over all articles
       Used for model comparison in the analytics dashboard.
       Not suitable for production scale (O(N) per query).

Also handles:
    - Search history logging (per user per query)
"""

from __future__ import annotations

import json
import time
from typing import List, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session

from app.database.models import Article, SearchHistory
from app.services.embedding_service import get_embedding_service
from app.services.faiss_service import get_faiss_service
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class RetrievalService:
    """
    Orchestrates query embedding, vector search, and DB article retrieval.
    """

    def __init__(self) -> None:
        self._embedding_svc = get_embedding_service()
        self._faiss_svc = get_faiss_service()

    # ── Semantic Search (SBERT + FAISS) ──────────────────────────────────────

    def semantic_search(
        self,
        query: str,
        db: Session,
        top_k: int = 10,
    ) -> Tuple[List[dict], float]:
        """
        Perform semantic search using SBERT embeddings + FAISS.

        Steps:
            1. Embed the query using SBERT
            2. Search FAISS for top-K nearest vectors (cosine similarity)
            3. Fetch matching articles from PostgreSQL
            4. Return results ordered by similarity score

        Args:
            query:  User's search query string.
            db:     SQLAlchemy database session.
            top_k:  Number of results to return.

        Returns:
            Tuple of:
                - List of dicts: [{"article": Article, "similarity_score": float}]
                - elapsed_ms: float — retrieval time in milliseconds
        """
        t0 = time.perf_counter()

        # Step 1: Embed query
        query_embedding = self._embedding_svc.embed_text(query)

        # Step 2: FAISS search → [(article_id, score), ...]
        raw_results = self._faiss_svc.search(query_embedding, top_k=top_k)

        if not raw_results:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            logger.info("Semantic search returned 0 results for query: '%s'", query)
            return [], elapsed_ms

        # Step 3: Fetch articles from DB in one query
        article_ids = [aid for aid, _ in raw_results]
        score_map = {aid: score for aid, score in raw_results}

        articles = (
            db.query(Article)
            .filter(Article.id.in_(article_ids))
            .all()
        )
        articles_by_id = {a.id: a for a in articles}

        # Step 4: Build results preserving FAISS ranking order
        results = []
        for aid, score in raw_results:
            if aid in articles_by_id:
                results.append({
                    "article": articles_by_id[aid],
                    "similarity_score": round(score, 4),
                })

        elapsed_ms = (time.perf_counter() - t0) * 1000
        logger.info(
            "Semantic search: query='%s' results=%d time=%.1fms",
            query, len(results), elapsed_ms,
        )
        return results, elapsed_ms

    # ── TF-IDF Baseline Search ────────────────────────────────────────────────

    def tfidf_search(
        self,
        query: str,
        db: Session,
        top_k: int = 10,
    ) -> Tuple[List[dict], float]:
        """
        Perform baseline TF-IDF + cosine similarity search.

        Note: This fetches ALL articles each time — O(N) complexity.
        Suitable only for model comparison on small datasets.
        Not recommended for production use.

        Args:
            query:  User's search query string.
            db:     SQLAlchemy database session.
            top_k:  Number of results to return.

        Returns:
            Tuple of:
                - List of dicts: [{"article": Article, "similarity_score": float}]
                - elapsed_ms: float — retrieval time in milliseconds
        """
        t0 = time.perf_counter()

        # Fetch all articles
        articles = db.query(Article).all()
        if not articles:
            return [], (time.perf_counter() - t0) * 1000

        # Build TF-IDF matrix over all article contents
        corpus = [f"{a.title} {a.content}" for a in articles]
        tfidf = TfidfVectorizer(
            max_features=10000,
            sublinear_tf=True,
            strip_accents="unicode",
            analyzer="word",
        )
        tfidf_matrix = tfidf.fit_transform(corpus)   # (N, vocab)
        query_vec = tfidf.transform([query])           # (1, vocab)

        # Cosine similarity between query and all articles
        scores = cosine_similarity(query_vec, tfidf_matrix).flatten()

        # Get top-K indices sorted by descending score
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = [
            {
                "article": articles[i],
                "similarity_score": round(float(scores[i]), 4),
            }
            for i in top_indices
            if scores[i] > 0  # Only return articles with some similarity
        ]

        elapsed_ms = (time.perf_counter() - t0) * 1000
        logger.info(
            "TF-IDF search: query='%s' results=%d time=%.1fms",
            query, len(results), elapsed_ms,
        )
        return results, elapsed_ms

    # ── Search History Logging ────────────────────────────────────────────────

    def log_search(
        self,
        user_id: int,
        query: str,
        top_result_ids: List[int],
        db: Session,
    ) -> None:
        """
        Persist a search query and its top results to search_history.

        Used by the recommendation service to build user interest profiles.

        Args:
            user_id:        ID of the user who performed the search.
            query:          The search query string.
            top_result_ids: List of article IDs returned (in rank order).
            db:             SQLAlchemy database session.
        """
        try:
            entry = SearchHistory(
                user_id=user_id,
                query=query,
                top_result_ids=json.dumps(top_result_ids),
            )
            db.add(entry)
            db.commit()
            logger.debug(
                "Search logged: user_id=%d query='%s'",
                user_id, query,
            )
        except Exception as exc:
            logger.error("Failed to log search history: %s", exc)
            db.rollback()


# ── Factory ───────────────────────────────────────────────────────────────────

def get_retrieval_service() -> RetrievalService:
    """Return a new RetrievalService instance."""
    return RetrievalService()
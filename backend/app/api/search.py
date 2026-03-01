"""
Search API endpoints.

Routes:
    POST /api/v1/search/semantic → SBERT + FAISS semantic search
    POST /api/v1/search/tfidf   → TF-IDF baseline search

Both endpoints:
    - Require JWT authentication
    - Log the query to search_history (used by recommendation engine)
    - Return results with similarity scores and retrieval time
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.database.models import User
from app.database.schemas import (
    SearchRequest,
    SearchResponse,
    ArticleSearchResult,
    ArticleOut,
)
from app.services.retrieval_service import get_retrieval_service
from app.dependencies import get_current_user
from app.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/search", tags=["Search"])


# ── Semantic Search ───────────────────────────────────────────────────────────

@router.post(
    "/semantic",
    response_model=SearchResponse,
    summary="Semantic search using SBERT + FAISS",
    description=(
        "Convert the query to a Sentence-BERT embedding, "
        "then perform cosine similarity search over the FAISS index. "
        "Returns top-K articles ranked by semantic similarity."
    ),
)
def semantic_search(
    payload: SearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Perform semantic search using SBERT embeddings and FAISS.

    Pipeline:
        1. Preprocess and embed the query via SBERT (384-dim vector)
        2. Search FAISS IndexFlatIP for top-K nearest vectors
        3. Map FAISS positions → article DB IDs
        4. Fetch article records from PostgreSQL
        5. Log the search to user's search_history
        6. Return ranked results with similarity scores

    Args:
        payload: SearchRequest containing query string and optional top_k.

    Returns:
        SearchResponse with results list and retrieval time in milliseconds.
    """
    svc = get_retrieval_service()
    top_k = payload.top_k or settings.TOP_K

    results, elapsed_ms = svc.semantic_search(
        query=payload.query,
        db=db,
        top_k=top_k,
    )

    # Log search to history for recommendation engine
    top_result_ids = [r["article"].id for r in results]
    svc.log_search(
        user_id=current_user.id,
        query=payload.query,
        top_result_ids=top_result_ids,
        db=db,
    )

    logger.info(
        "Semantic search: user=%d query='%s' results=%d time=%.1fms",
        current_user.id, payload.query, len(results), elapsed_ms,
    )

    return SearchResponse(
        query=payload.query,
        results=[
            ArticleSearchResult(
                article=ArticleOut.model_validate(r["article"]),
                similarity_score=r["similarity_score"],
            )
            for r in results
        ],
        retrieval_time_ms=round(elapsed_ms, 2),
    )


# ── TF-IDF Baseline Search ────────────────────────────────────────────────────

@router.post(
    "/tfidf",
    response_model=SearchResponse,
    summary="Baseline TF-IDF search",
    description=(
        "Perform a TF-IDF + cosine similarity search over all articles. "
        "Intended for model comparison purposes. "
        "Note: O(N) complexity — not suitable for large-scale production use."
    ),
)
def tfidf_search(
    payload: SearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Perform baseline TF-IDF search for model comparison.

    Pipeline:
        1. Fetch all articles from PostgreSQL
        2. Build TF-IDF matrix over article content
        3. Transform query to TF-IDF vector
        4. Compute cosine similarity with all articles
        5. Return top-K results ranked by similarity

    Args:
        payload: SearchRequest containing query string and optional top_k.

    Returns:
        SearchResponse with results list and retrieval time in milliseconds.
    """
    svc = get_retrieval_service()
    top_k = payload.top_k or settings.TOP_K

    results, elapsed_ms = svc.tfidf_search(
        query=payload.query,
        db=db,
        top_k=top_k,
    )

    logger.info(
        "TF-IDF search: user=%d query='%s' results=%d time=%.1fms",
        current_user.id, payload.query, len(results), elapsed_ms,
    )

    return SearchResponse(
        query=payload.query,
        results=[
            ArticleSearchResult(
                article=ArticleOut.model_validate(r["article"]),
                similarity_score=r["similarity_score"],
            )
            for r in results
        ],
        retrieval_time_ms=round(elapsed_ms, 2),
    )
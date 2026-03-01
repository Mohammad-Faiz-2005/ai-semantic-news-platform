"""
Recommendation API endpoint.

Route:
    GET /api/v1/recommendations → Personalised article recommendations

Strategy:
    - Content-based filtering using user search history
    - Aggregates past query embeddings into a user interest vector
    - Searches FAISS for most similar unread articles
    - Falls back to latest articles if no history exists
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.database.models import User
from app.database.schemas import (
    RecommendationResponse,
    ArticleSearchResult,
    ArticleOut,
)
from app.services.recommendation_service import get_recommendation_service
from app.dependencies import get_current_user
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


# ── Get Recommendations ───────────────────────────────────────────────────────

@router.get(
    "",
    response_model=RecommendationResponse,
    summary="Get personalised article recommendations",
    description=(
        "Generate personalised article recommendations based on the "
        "current user's search history. "
        "Uses a mean-pooled interest vector of past query embeddings "
        "to find semantically similar unread articles via FAISS. "
        "Falls back to latest articles for new users with no search history."
    ),
)
def get_recommendations(
    top_k: int = Query(
        default=10,
        ge=1,
        le=50,
        description="Number of recommendations to return (1-50).",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return personalised recommendations for the authenticated user.

    Pipeline:
        1. Fetch user's last 50 search queries from search_history
        2. Embed each query using SBERT → (N, 384) matrix
        3. Mean pool → (384,) user interest vector
        4. L2-renormalise the interest vector
        5. Search FAISS for top-(K + seen) most similar articles
        6. Filter out already-seen article IDs
        7. Fetch remaining articles from PostgreSQL
        8. Return top-K recommendations

    Fallback:
        If user has no search history, return the most recently
        added articles with similarity_score = 0.0.

    Args:
        top_k: Number of recommendations to return.

    Returns:
        RecommendationResponse with recommendations list
        and the number of past queries used.
    """
    svc = get_recommendation_service()

    recommendations, num_queries_used = svc.recommend(
        user_id=current_user.id,
        db=db,
        top_k=top_k,
    )

    logger.info(
        "Recommendations: user=%d queries_used=%d results=%d",
        current_user.id, num_queries_used, len(recommendations),
    )

    return RecommendationResponse(
        recommendations=[
            ArticleSearchResult(
                article=ArticleOut.model_validate(r["article"]),
                similarity_score=r["similarity_score"],
            )
            for r in recommendations
        ],
        based_on_queries=num_queries_used,
    )
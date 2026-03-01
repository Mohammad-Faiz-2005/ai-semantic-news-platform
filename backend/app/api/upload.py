"""
Article upload API endpoints (Admin only).

Routes:
    POST /api/v1/upload          → Upload new article and index in FAISS
    GET  /api/v1/upload/articles → List all articles (admin)

Access: Admin JWT required for all endpoints.

On upload:
    1. Article is saved to PostgreSQL
    2. SBERT embedding is generated for title + content
    3. Embedding is added to the FAISS index
    4. FAISS index is persisted to disk
    5. Article is marked as embedding_generated=True
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.database.models import Article, User
from app.database.schemas import (
    ArticleCreate,
    ArticleOut,
    UploadResponse,
)
from app.services.embedding_service import get_embedding_service
from app.services.faiss_service import get_faiss_service
from app.dependencies import require_admin
from app.utils.preprocessing import combine_title_content
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/upload", tags=["Upload"])


# ── Upload Article ────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and index a new article (Admin)",
    description=(
        "Admin-only endpoint. "
        "Saves a new article to PostgreSQL, generates its SBERT embedding, "
        "adds it to the FAISS index, and persists the index to disk. "
        "The article is immediately searchable after upload."
    ),
)
def upload_article(
    payload: ArticleCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Upload a new article and add it to the FAISS index.

    Steps:
        1. Validate and save article to PostgreSQL
        2. Combine title + content for embedding
        3. Generate SBERT embedding (384-dim, L2-normalised)
        4. Add embedding to FAISS IndexFlatIP
        5. Persist FAISS index to disk
        6. Mark article as embedding_generated=True
        7. Return article data with success message

    Args:
        payload: ArticleCreate with title, content, domain, source.

    Returns:
        UploadResponse with article data and success message.

    Raises:
        403 Forbidden - If the user is not an admin.
        422 Unprocessable Entity - If content is too short.
    """
    # Validate content length
    if len(payload.content.strip()) < 20:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Article content must be at least 20 characters.",
        )

    # Step 1: Save article to PostgreSQL
    article = Article(
        title=payload.title.strip(),
        content=payload.content.strip(),
        domain=payload.domain.strip() if payload.domain else None,
        source=payload.source.strip() if payload.source else None,
        embedding_generated=False,
    )
    db.add(article)
    db.commit()
    db.refresh(article)

    logger.info(
        "Article saved: id=%d title='%s'",
        article.id, article.title[:50],
    )

    # Step 2: Combine title + content for embedding
    text_to_embed = combine_title_content(article.title, article.content)

    # Step 3: Generate SBERT embedding
    emb_svc = get_embedding_service()
    embedding = emb_svc.embed_text(text_to_embed)

    # Step 4: Add to FAISS index
    faiss_svc = get_faiss_service()
    faiss_svc.add(article.id, embedding)

    # Step 5: Persist FAISS index
    faiss_svc.save()

    # Step 6: Mark article as embedded
    article.embedding_generated = True
    db.commit()
    db.refresh(article)

    logger.info(
        "Article indexed in FAISS: id=%d total_vectors=%d",
        article.id, faiss_svc.total_vectors,
    )

    return UploadResponse(
        article=ArticleOut.model_validate(article),
        message=(
            f"Article '{article.title}' uploaded and indexed successfully. "
            f"FAISS index now contains {faiss_svc.total_vectors} vectors."
        ),
    )


# ── List Articles ─────────────────────────────────────────────────────────────

@router.get(
    "/articles",
    response_model=list[ArticleOut],
    summary="List all articles (Admin)",
    description="Return a paginated list of all articles in the database.",
)
def list_articles(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Return a paginated list of all articles.

    Args:
        skip:  Number of records to skip (for pagination).
        limit: Maximum number of records to return.

    Returns:
        List of ArticleOut objects.
    """
    articles = (
        db.query(Article)
        .order_by(Article.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    logger.info(
        "Admin article list: skip=%d limit=%d returned=%d",
        skip, limit, len(articles),
    )

    return [ArticleOut.model_validate(a) for a in articles]
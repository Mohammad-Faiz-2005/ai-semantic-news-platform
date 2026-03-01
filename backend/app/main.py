"""
FastAPI application entry point.

Responsibilities:
- Create FastAPI app instance
- Register all routers
- Configure CORS middleware
- Handle startup/shutdown lifecycle:
    * Create DB tables
    * Warm-up SBERT model
    * Load FAISS index from disk
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.logging_config import configure_logging, get_logger
from app.database.db import engine
from app.database.models import Base
from app.services.faiss_service import get_faiss_service
from app.models.sbert_model import get_sbert_model
from app.api import auth, search, recommendation, upload, analytics

# Configure logging before anything else
configure_logging()
logger = get_logger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup / shutdown lifecycle handler.

    Startup:
        1. Create all PostgreSQL tables (idempotent via CREATE IF NOT EXISTS)
        2. Pre-load SBERT model into memory (downloads on first run)
        3. Load FAISS index from disk (or start fresh if not found)

    Shutdown:
        - Log graceful exit message
    """
    logger.info("=" * 60)
    logger.info("Starting AI Semantic News Platform...")
    logger.info("=" * 60)

    # Step 1: Create all DB tables
    logger.info("Ensuring database tables exist...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ready.")

    # Step 2: Warm up SBERT model
    # This downloads the model on first run (~90MB) and caches it
    logger.info("Loading SBERT model (this may take a moment on first run)...")
    get_sbert_model()
    logger.info("SBERT model ready.")

    # Step 3: Load FAISS index
    logger.info("Loading FAISS index...")
    faiss_svc = get_faiss_service()
    logger.info("FAISS index ready (%d vectors).", faiss_svc.total_vectors)

    logger.info("Application startup complete. Listening on port 8000.")

    yield  # ← Application runs here

    logger.info("Application shutting down gracefully.")


# ── App Instance ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="AI Semantic News Retrieval API",
    version="1.0.0",
    description=(
        "Semantic search and personalised recommendations for news articles "
        "using Sentence-BERT embeddings and FAISS vector indexing."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ── CORS Middleware ───────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(auth.router,           prefix="/api/v1")
app.include_router(search.router,         prefix="/api/v1")
app.include_router(recommendation.router, prefix="/api/v1")
app.include_router(upload.router,         prefix="/api/v1")
app.include_router(analytics.router,      prefix="/api/v1")


# ── Health Check ─────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
def health_check():
    """
    Simple health check endpoint.
    Used by Docker healthcheck and load balancers.
    """
    return {
        "status": "ok",
        "service": "ai-semantic-news-api",
        "version": "1.0.0",
    }
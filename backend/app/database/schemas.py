"""
Pydantic schemas for request validation and response serialisation.

Organised by domain:
    - User / Auth schemas
    - Article schemas
    - Search schemas
    - Recommendation schemas
    - Analytics schemas
    - Upload schemas
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr


# ── User / Auth ───────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    """Request body for POST /auth/register"""
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    """Request body for POST /auth/login"""
    email: EmailStr
    password: str


class UserOut(BaseModel):
    """User data returned in API responses (never includes password)"""
    id: int
    name: str
    email: EmailStr
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Response body for login and register endpoints"""
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ── Article ───────────────────────────────────────────────────────────────────

class ArticleCreate(BaseModel):
    """Request body for POST /upload"""
    title: str
    content: str
    domain: Optional[str] = None
    source: Optional[str] = None


class ArticleOut(BaseModel):
    """Article data returned in API responses"""
    id: int
    title: str
    content: str
    domain: Optional[str]
    source: Optional[str]
    created_at: datetime
    embedding_generated: bool

    model_config = {"from_attributes": True}


class ArticleSearchResult(BaseModel):
    """A single search result: article + its similarity score"""
    article: ArticleOut
    similarity_score: float


# ── Search ────────────────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    """Request body for POST /search/semantic and /search/tfidf"""
    query: str
    top_k: Optional[int] = 10


class SearchResponse(BaseModel):
    """Response body for search endpoints"""
    query: str
    results: List[ArticleSearchResult]
    retrieval_time_ms: float


# ── Recommendation ────────────────────────────────────────────────────────────

class RecommendationResponse(BaseModel):
    """Response body for GET /recommendations"""
    recommendations: List[ArticleSearchResult]
    based_on_queries: int   # Number of past queries used to build interest vector


# ── Analytics ─────────────────────────────────────────────────────────────────

class ModelMetrics(BaseModel):
    """Metrics for a single ML model"""
    model_name: str
    accuracy: Optional[float]
    precision: Optional[float]
    recall: Optional[float]
    f1_score: Optional[float]
    precision_at_k: Optional[float]
    recall_at_k: Optional[float]
    retrieval_time_ms: Optional[float]


class AnalyticsResponse(BaseModel):
    """Response body for GET /analytics"""
    total_articles: int
    total_users: int
    total_searches: int
    model_metrics: List[ModelMetrics]
    top_domains: List[dict]


# ── Upload ────────────────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    """Response body for POST /upload"""
    article: ArticleOut
    message: str
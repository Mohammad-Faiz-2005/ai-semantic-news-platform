"""
SQLAlchemy ORM models.

Tables:
    - User          → stores registered users
    - Article       → stores news articles
    - SearchHistory → stores user search queries and results
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database.db import Base


# ── User ──────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    name            = Column(String(120), nullable=False)
    email           = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role            = Column(String(20), default="user", nullable=False)  # "user" | "admin"
    created_at      = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active       = Column(Boolean, default=True, nullable=False)

    # One user → many search history entries
    search_history = relationship(
        "SearchHistory",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"


# ── Article ───────────────────────────────────────────────────────────────────

class Article(Base):
    __tablename__ = "articles"

    id                  = Column(Integer, primary_key=True, index=True)
    title               = Column(String(512), nullable=False)
    content             = Column(Text, nullable=False)
    domain              = Column(String(120), nullable=True)   # e.g. "technology", "sports"
    source              = Column(String(255), nullable=True)   # e.g. "BBC News"
    created_at          = Column(DateTime, default=datetime.utcnow, nullable=False)
    embedding_generated = Column(Boolean, default=False, nullable=False)
    # True once the article's embedding has been added to FAISS

    def __repr__(self) -> str:
        return f"<Article id={self.id} title={self.title[:40]}>"


# ── SearchHistory ─────────────────────────────────────────────────────────────

class SearchHistory(Base):
    __tablename__ = "search_history"

    id             = Column(Integer, primary_key=True, index=True)
    user_id        = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    query          = Column(Text, nullable=False)
    top_result_ids = Column(Text, nullable=True)
    # Stored as JSON-encoded list of article IDs
    # e.g. "[1, 5, 12, 3, 7]"
    timestamp      = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Many search history entries → one user
    user = relationship("User", back_populates="search_history")

    def __repr__(self) -> str:
        return f"<SearchHistory id={self.id} user_id={self.user_id} query={self.query[:30]}>"
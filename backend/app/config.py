"""
Application configuration using Pydantic Settings.

Reads all values from environment variables or a .env file.
Provides a singleton `settings` instance used throughout the app.
"""

from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    All application settings with types, defaults, and env var mappings.
    Values are read from environment variables (case-sensitive).
    Falls back to .env file if present.
    """

    # ── Database ──────────────────────────────────────────────
    DATABASE_URL: str = Field(..., env="DATABASE_URL")

    # ── JWT / Security ────────────────────────────────────────
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALGORITHM: str = Field("HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(60, env="ACCESS_TOKEN_EXPIRE_MINUTES")

    # ── FAISS / ML ────────────────────────────────────────────
    FAISS_INDEX_PATH: str = Field(
        "vector_store/faiss_index.bin",
        env="FAISS_INDEX_PATH"
    )
    ID_MAPPING_PATH: str = Field(
        "vector_store/id_mapping.pkl",
        env="ID_MAPPING_PATH"
    )
    SBERT_MODEL_NAME: str = Field(
        "all-MiniLM-L6-v2",
        env="SBERT_MODEL_NAME"
    )
    TOP_K: int = Field(10, env="TOP_K")

    # ── App ───────────────────────────────────────────────────
    ENVIRONMENT: str = Field("development", env="ENVIRONMENT")
    BACKEND_CORS_ORIGINS: str = Field(
        "http://localhost:5173,http://localhost:3000",
        env="BACKEND_CORS_ORIGINS"
    )

    @property
    def cors_origins(self) -> List[str]:
        """
        Parse comma-separated CORS origins string into a list.
        Example: "http://localhost:5173,http://localhost:3000"
             → ["http://localhost:5173", "http://localhost:3000"]
        """
        return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",")]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    class Config:
        env_file = ".env"
        case_sensitive = True


# ── Singleton instance ────────────────────────────────────────────────────────
# Import this throughout the app: from app.config import settings
settings = Settings()
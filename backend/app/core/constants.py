"""
Application-wide constants.

Centralised here to avoid magic numbers/strings scattered across the codebase.
"""

# ── FAISS / Embeddings ────────────────────────────────────────────────────────

# Output dimension of all-MiniLM-L6-v2 Sentence-BERT model
EMBEDDING_DIM = 384

# ── User Roles ────────────────────────────────────────────────────────────────

ROLE_USER = "user"
ROLE_ADMIN = "admin"

# ── Recommendation ────────────────────────────────────────────────────────────

# Maximum number of past search queries used to build user interest vector
MAX_HISTORY_ARTICLES = 50

# Default number of results returned by search and recommendation endpoints
DEFAULT_TOP_K = 10

# ── Text Processing ───────────────────────────────────────────────────────────

# Approximate max tokens for SBERT input (1 token ≈ 4 characters)
MAX_EMBEDDING_TOKENS = 512

# ── Analytics ─────────────────────────────────────────────────────────────────

# Number of top domains to show in analytics dashboard
TOP_DOMAINS_LIMIT = 10
"""
Security utilities: password hashing and JWT token management.

Uses:
    - passlib[bcrypt] for password hashing
    - python-jose for JWT creation and verification
"""

from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# ── Password Hashing ──────────────────────────────────────────────────────────

# bcrypt context — automatically handles salt generation and hash versioning
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a plain-text password using bcrypt.

    Args:
        password: Plain-text password string.

    Returns:
        Bcrypt hashed password string (safe to store in DB).
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against a bcrypt hash.

    Args:
        plain_password:  The raw password from the login request.
        hashed_password: The stored bcrypt hash from the database.

    Returns:
        True if the password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT Tokens ────────────────────────────────────────────────────────────────

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a signed JWT access token.

    Token payload structure:
        {
            "sub": "<user_id>",   ← subject (user identifier)
            "exp": <unix_ts>,     ← expiration timestamp
            ... any extra data
        }

    Args:
        data:          Dictionary of claims to include in the token payload.
                       Should contain at least {"sub": str(user_id)}.
        expires_delta: Custom expiration duration.
                       Defaults to settings.ACCESS_TOKEN_EXPIRE_MINUTES.

    Returns:
        Encoded JWT string.
    """
    to_encode = data.copy()

    expire = datetime.utcnow() + (
        expires_delta
        if expires_delta
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})

    token = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    return token


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and verify a JWT access token.

    Validates:
        - Signature (using SECRET_KEY)
        - Expiration (exp claim)
        - Algorithm (must match settings.ALGORITHM)

    Args:
        token: JWT string from Authorization header.

    Returns:
        Decoded payload dict if valid, None if invalid or expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload

    except JWTError as exc:
        logger.debug("JWT decode failed: %s", exc)
        return None
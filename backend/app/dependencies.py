"""
FastAPI dependency injection helpers.

These are injected into route handlers via Depends().
Provides:
    - get_current_user: validates JWT and returns the authenticated User
    - require_admin: additionally enforces admin role
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.database.models import User
from app.utils.security import decode_access_token
from app.core.constants import ROLE_ADMIN

# HTTPBearer extracts the token from "Authorization: Bearer <token>"
bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency: Decode JWT token and return the authenticated User ORM object.

    Raises:
        401 - If token is missing, invalid, or expired
        401 - If the user does not exist or is inactive
    """
    token = credentials.credentials

    # Decode and verify the JWT
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user ID from token payload
    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is missing required subject claim.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Look up user in the database
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with this token no longer exists.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This account has been deactivated.",
        )

    return user


def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency: Enforce that the current user has the 'admin' role.

    Raises:
        403 - If the user does not have admin privileges
    """
    if current_user.role != ROLE_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires administrator privileges.",
        )
    return current_user
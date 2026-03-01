"""
Authentication API endpoints.

Routes:
    POST /api/v1/auth/register → Create new user account
    POST /api/v1/auth/login    → Authenticate and return JWT
    GET  /api/v1/auth/me       → Return current user profile
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.database.models import User
from app.database.schemas import (
    UserCreate,
    UserLogin,
    UserOut,
    TokenResponse,
)
from app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
)
from app.dependencies import get_current_user
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ── Register ──────────────────────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description=(
        "Create a new user account. "
        "Returns a JWT access token and user profile on success."
    ),
)
def register(
    payload: UserCreate,
    db: Session = Depends(get_db),
):
    """
    Register a new user account.

    Steps:
        1. Check email is not already registered
        2. Hash the password with bcrypt
        3. Insert user into the database
        4. Return JWT token + user profile

    Raises:
        409 Conflict - If email is already registered
    """
    # Check for duplicate email
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An account with email '{payload.email}' already exists.",
        )

    # Validate password length
    if len(payload.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 6 characters long.",
        )

    # Create user record
    user = User(
        name=payload.name.strip(),
        email=payload.email.lower().strip(),
        hashed_password=hash_password(payload.password),
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Generate JWT token
    access_token = create_access_token(data={"sub": str(user.id)})

    logger.info("New user registered: id=%d email=%s", user.id, user.email)

    return TokenResponse(
        access_token=access_token,
        user=UserOut.model_validate(user),
    )


# ── Login ─────────────────────────────────────────────────────────────────────

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and get JWT token",
    description=(
        "Authenticate with email and password. "
        "Returns a JWT access token and user profile on success."
    ),
)
def login(
    payload: UserLogin,
    db: Session = Depends(get_db),
):
    """
    Authenticate a user and return a JWT access token.

    Steps:
        1. Look up user by email
        2. Verify bcrypt password hash
        3. Return JWT token + user profile

    Raises:
        401 Unauthorized - If email not found or password incorrect
    """
    # Look up user by email
    user = db.query(User).filter(
        User.email == payload.email.lower().strip()
    ).first()

    # Verify password (use constant-time comparison via passlib)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This account has been deactivated.",
        )

    # Generate JWT token
    access_token = create_access_token(data={"sub": str(user.id)})

    logger.info("User logged in: id=%d email=%s", user.id, user.email)

    return TokenResponse(
        access_token=access_token,
        user=UserOut.model_validate(user),
    )


# ── Get Current User ──────────────────────────────────────────────────────────

@router.get(
    "/me",
    response_model=UserOut,
    summary="Get current user profile",
    description="Return the profile of the currently authenticated user.",
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    """
    Return the authenticated user's profile.

    Requires: Valid JWT Bearer token in Authorization header.
    """
    return UserOut.model_validate(current_user)
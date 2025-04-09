"""
Authentication endpoints module.

This module contains endpoints for user authentication.
"""
from datetime import datetime, timedelta, timezone # Added timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_session
from app.core.security import create_access_token, verify_password
from app.models.user import User, UserRead # Import UserRead
from app.schemas.token import Token

router = APIRouter()


@router.post("/token", response_model=Token)
def login_access_token(
    session: Session = Depends(get_session),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.

    Args:
        session: Database session
        form_data: OAuth2 password request form

    Returns:
        Token: Access token

    Raises:
        HTTPException: If authentication fails
    """
    # Find user by email
    user = session.exec(
        select(User).where(User.email == form_data.username)
    ).first()

    # Check if user exists and password is correct
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # Update last login time (use timezone aware)
    user.last_login = datetime.now(timezone.utc)
    session.add(user)
    session.commit()
    session.refresh(user)

    return {
        "access_token": create_access_token(
            subject=user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


# Update response model to UserRead which should include linkedin_id
@router.post("/test-token", response_model=UserRead)
def test_token(
    current_user: User = Depends(get_current_user),
    # session: Session = Depends(get_session), # Session no longer needed here
) -> Any:
    """
    Test access token and return current user info including LinkedIn status.

    Args:
        current_user: Current authenticated user

    Returns:
        UserRead: User information including linkedin_id
    """
    # The current_user object obtained from get_current_user already contains
    # all fields, including linkedin_id. We just need to return it.
    # Pydantic/FastAPI will automatically handle converting the User model
    # instance to the UserRead response model.
    return current_user

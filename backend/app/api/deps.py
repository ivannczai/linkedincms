"""
API dependencies module.

This module contains dependencies for FastAPI endpoints.
"""
from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from jose.exceptions import JWTError
from pydantic import ValidationError, BaseModel
from sqlmodel import Session, select

from app.core.config import settings
from app.core.database import get_session
from app.models.user import User, UserRole
from app.schemas.token import TokenData, TokenPayload
from app.crud import client as crud_client

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")


def get_current_user(
    session: Session = Depends(get_session),
    token: str = Depends(oauth2_scheme),
) -> User:
    """
    Get the current authenticated user.
    
    Args:
        session: Database session
        token: JWT token
        
    Returns:
        User: The authenticated user
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Decode the JWT token
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=["HS256"]
        )
        token_data = TokenPayload(**payload)
        
        # Check if token is expired
        if token_data.exp is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Get user ID from token
        user_id: Optional[int] = token_data.sub
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Get user from database
        user = session.exec(select(User).where(User.id == user_id)).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return user
        
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get the current active user.
    
    Args:
        current_user: The current authenticated user
        
    Returns:
        User: The current active user
        
    Raises:
        HTTPException: If the user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    return current_user


def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get the current admin user.
    
    Args:
        current_user: The current authenticated user
        
    Returns:
        User: The current admin user
        
    Raises:
        HTTPException: If the user is not an admin
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user


class CurrentClientUser(BaseModel):
    id: int
    email: str
    client_id: int
    role: str
    is_active: bool
    full_name: str


def get_current_client_user(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> CurrentClientUser:
    """
    Get the current client user with client_id.
    """
    if current_user.role != UserRole.CLIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    client_profile = crud_client.get_by_user_id(session, user_id=current_user.id)
    if not client_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client profile not found",
        )
    return CurrentClientUser(
        id=current_user.id,
        email=current_user.email,
        client_id=client_profile.id,
        role=current_user.role,
        is_active=current_user.is_active,
        full_name=current_user.full_name,
    )

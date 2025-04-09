"""
Users API endpoints module.

This module contains API endpoints for user management.
"""
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.api.deps import get_current_admin_user, get_current_user, get_session
from app.crud import user as user_crud
from app.models.user import User, UserCreate, UserRead, UserUpdate

router = APIRouter()


@router.get("/", response_model=List[UserRead])
def read_users(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve users.
    
    Args:
        session: Database session
        current_user: Current admin user
        skip: Number of users to skip
        limit: Maximum number of users to return
        
    Returns:
        List[UserRead]: List of users
    """
    users = session.exec(select(User).offset(skip).limit(limit)).all()
    return users


@router.get("/me", response_model=UserRead)
def read_user_me(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get current user.
    
    Args:
        current_user: Current user
        
    Returns:
        UserRead: Current user
    """
    return current_user


@router.get("/{user_id}", response_model=UserRead)
def read_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    """
    Get user by ID.
    
    Args:
        user_id: User ID
        session: Database session
        current_user: Current admin user
        
    Returns:
        UserRead: User
        
    Raises:
        HTTPException: If user not found
    """
    user = user_crud.get(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.post("/", response_model=UserRead)
def create_user(
    user_in: UserCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    """
    Create new user.
    
    Args:
        user_in: User creation data
        session: Database session
        current_user: Current admin user
        
    Returns:
        UserRead: Created user
        
    Raises:
        HTTPException: If user with same email already exists
    """
    user = user_crud.get_by_email(session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )
    user = user_crud.create(session, obj_in=user_in)
    return user


@router.put("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    user_in: UserUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    """
    Update a user.
    
    Args:
        user_id: User ID
        user_in: User update data
        session: Database session
        current_user: Current admin user
        
    Returns:
        UserRead: Updated user
        
    Raises:
        HTTPException: If user not found
    """
    user = user_crud.get(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    user = user_crud.update(session, db_obj=user, obj_in=user_in)
    return user


@router.put("/me", response_model=UserRead)
def update_user_me(
    user_in: UserUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update current user.
    
    Args:
        user_in: User update data
        session: Database session
        current_user: Current user
        
    Returns:
        UserRead: Updated user
    """
    user = user_crud.update(session, db_obj=current_user, obj_in=user_in)
    return user

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
    # Ensure relationships needed for UserRead are loaded if necessary
    # (SQLModel might handle this automatically depending on access patterns)
    users = session.exec(select(User).offset(skip).limit(limit)).all()
    # Manually populate client_id for each user before returning
    users_read = []
    for user in users:
        user_data = UserRead.model_validate(user) # Validate against schema first
        if user.client_profile:
            user_data.client_id = user.client_profile.id
        users_read.append(user_data)
    return users_read


@router.get("/me", response_model=UserRead)
def read_user_me(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session) # Add session dependency
) -> Any:
    """
    Get current user. Includes client_id if applicable.

    Args:
        current_user: Current user from token dependency
        session: Database session

    Returns:
        UserRead: Current user data including client_id
    """
    # Ensure the client_profile relationship is loaded.
    # The dependency might already load it, but explicit refresh/load can ensure it.
    # Refreshing the user object from the session might load relationships.
    session.refresh(current_user) # Attempt to refresh/load relationships

    # Create the UserRead object and manually set client_id
    user_data = UserRead.model_validate(current_user)
    if current_user.client_profile:
        user_data.client_id = current_user.client_profile.id

    return user_data


@router.get("/{user_id}", response_model=UserRead)
def read_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    """
    Get user by ID. Includes client_id if applicable.

    Args:
        user_id: User ID
        session: Database session
        current_user: Current admin user

    Returns:
        UserRead: User data including client_id

    Raises:
        HTTPException: If user not found
    """
    user = user_crud.get(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    # Manually populate client_id before returning
    user_data = UserRead.model_validate(user)
    if user.client_profile:
        user_data.client_id = user.client_profile.id
    return user_data


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
        UserRead: Created user data including client_id

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
    # Manually populate client_id before returning
    user_data = UserRead.model_validate(user)
    if user.client_profile: # Should be None for direct user creation
        user_data.client_id = user.client_profile.id
    return user_data


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
        UserRead: Updated user data including client_id

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
    # Manually populate client_id before returning
    user_data = UserRead.model_validate(user)
    if user.client_profile:
        user_data.client_id = user.client_profile.id
    return user_data


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
        UserRead: Updated user data including client_id
    """
    user = user_crud.update(session, db_obj=current_user, obj_in=user_in)
    # Manually populate client_id before returning
    user_data = UserRead.model_validate(user)
    if user.client_profile:
        user_data.client_id = user.client_profile.id
    return user_data

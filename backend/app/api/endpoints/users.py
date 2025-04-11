"""
Users API endpoints module.

This module contains API endpoints for user management.
"""
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.api.deps import get_current_admin_user, get_current_user, get_session
from app.crud import user as user_crud
from app.crud import client as client_crud # Import client crud
from app.models.user import User, UserCreate, UserRead, UserUpdate, UserRole # Import UserRole

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
    """
    users = session.exec(select(User).offset(skip).limit(limit)).all()
    # Manually populate client_id for each user before returning
    users_read = []
    for user in users:
        user_data = UserRead.model_validate(user)
        # Eagerly load or query profile if needed
        profile = client_crud.get_by_user_id(session, user_id=user.id)
        if profile:
            user_data.client_id = profile.id
        users_read.append(user_data)
    return users_read


@router.get("/me", response_model=UserRead)
def read_user_me(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session) # Add session dependency
) -> Any:
    """
    Get current user. Includes client_id if applicable.
    """
    # Create the UserRead object from the current user
    user_data = UserRead.model_validate(current_user)

    # Explicitly query for the client profile if the user is a client
    if current_user.role == UserRole.CLIENT:
        client_profile = client_crud.get_by_user_id(session, user_id=current_user.id)
        if client_profile:
            user_data.client_id = client_profile.id
        else:
            # Log a warning if a client user has no profile - indicates data inconsistency
            print(f"Warning: Client user {current_user.email} (ID: {current_user.id}) has no associated client profile.")

    return user_data


@router.get("/{user_id}", response_model=UserRead)
def read_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    """
    Get user by ID. Includes client_id if applicable.
    """
    user = user_crud.get(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    # Manually populate client_id before returning
    user_data = UserRead.model_validate(user)
    if user.role == UserRole.CLIENT:
        profile = client_crud.get_by_user_id(session, user_id=user.id)
        if profile:
            user_data.client_id = profile.id
    return user_data


@router.post("/", response_model=UserRead)
def create_user(
    user_in: UserCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    """
    Create new user.
    """
    user = user_crud.get_by_email(session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )
    user = user_crud.create(session, obj_in=user_in)
    # Manually populate client_id before returning (will be None here)
    user_data = UserRead.model_validate(user)
    user_data.client_id = None # Explicitly set to None as profile is not created here
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
    if user.role == UserRole.CLIENT:
        profile = client_crud.get_by_user_id(session, user_id=user.id)
        if profile:
            user_data.client_id = profile.id
    return user_data


@router.put("/me", response_model=UserRead)
def update_user_me(
    user_in: UserUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update current user.
    """
    user = user_crud.update(session, db_obj=current_user, obj_in=user_in)
    # Manually populate client_id before returning
    user_data = UserRead.model_validate(user)
    if user.role == UserRole.CLIENT:
        profile = client_crud.get_by_user_id(session, user_id=user.id)
        if profile:
            user_data.client_id = profile.id
    return user_data

"""
User CRUD operations module.

This module contains CRUD operations for the User model.
"""
from typing import Any, Dict, Optional, Union
from datetime import datetime # Import datetime

from sqlmodel import Session, select

from app.core.security import get_password_hash, verify_password, encrypt_data # Import encrypt_data
from app.models.user import User, UserCreate, UserUpdate


def get(session: Session, user_id: int) -> Optional[User]:
    """
    Get a user by ID.

    Args:
        session: Database session
        user_id: User ID

    Returns:
        Optional[User]: User if found, None otherwise
    """
    return session.get(User, user_id)


def get_by_email(session: Session, email: str) -> Optional[User]:
    """
    Get a user by email.

    Args:
        session: Database session
        email: User email

    Returns:
        Optional[User]: User if found, None otherwise
    """
    return session.exec(select(User).where(User.email == email)).first()


def create(session: Session, obj_in: UserCreate) -> User:
    """
    Create a new user.

    Args:
        session: Database session
        obj_in: User creation data

    Returns:
        User: Created user
    """
    db_obj = User(
        email=obj_in.email,
        hashed_password=get_password_hash(obj_in.password),
        full_name=obj_in.full_name,
        role=obj_in.role,
        is_active=obj_in.is_active,
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update(
    session: Session,
    db_obj: User,
    obj_in: Union[UserUpdate, Dict[str, Any]]
) -> User:
    """
    Update a user's general details.

    Args:
        session: Database session
        db_obj: User to update
        obj_in: User update data (UserUpdate schema or dict)

    Returns:
        User: Updated user
    """
    if isinstance(obj_in, dict):
        update_data = obj_in
    else:
        # Use exclude_unset=True to only update fields provided in the Pydantic model
        update_data = obj_in.dict(exclude_unset=True)

    # Hash password if provided
    if "password" in update_data and update_data["password"]:
        hashed_password = get_password_hash(update_data["password"])
        update_data["hashed_password"] = hashed_password
    # Remove password from update_data if it was present, even if None/empty
    if "password" in update_data:
        del update_data["password"]

    # Update user attributes
    for field, value in update_data.items():
        setattr(db_obj, field, value)

    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_linkedin_details(
    session: Session,
    db_obj: User,
    linkedin_data: Dict[str, Any]
) -> User:
    """
    Update a user's LinkedIn integration details, encrypting the access token.

    Args:
        session: Database session
        db_obj: User object to update
        linkedin_data: Dictionary containing LinkedIn details like:
                       'linkedin_id', 'linkedin_access_token',
                       'linkedin_token_expires_at', 'linkedin_scopes'

    Returns:
        User: Updated user object
    """
    db_obj.linkedin_id = linkedin_data.get("linkedin_id", db_obj.linkedin_id)
    db_obj.linkedin_token_expires_at = linkedin_data.get("linkedin_token_expires_at", db_obj.linkedin_token_expires_at)
    db_obj.linkedin_scopes = linkedin_data.get("linkedin_scopes", db_obj.linkedin_scopes)

    # Encrypt the access token before saving
    access_token = linkedin_data.get("linkedin_access_token")
    if access_token:
        db_obj.linkedin_access_token = encrypt_data(access_token)
    else:
        # Handle case where token might be explicitly set to None (e.g., disconnect)
        db_obj.linkedin_access_token = None

    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def authenticate(session: Session, email: str, password: str) -> Optional[User]:
    """
    Authenticate a user.

    Args:
        session: Database session
        email: User email
        password: User password

    Returns:
        Optional[User]: User if authenticated, None otherwise
    """
    user = get_by_email(session, email=email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def is_active(user: User) -> bool:
    """
    Check if a user is active.

    Args:
        user: User to check

    Returns:
        bool: True if user is active, False otherwise
    """
    return user.is_active


def is_admin(user: User) -> bool:
    """
    Check if a user is an admin.

    Args:
        user: User to check

    Returns:
        bool: True if user is an admin, False otherwise
    """
    return user.role == "admin"

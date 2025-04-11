"""
ClientProfile CRUD operations module.

This module contains CRUD operations for the ClientProfile model.
"""
from typing import List, Optional, Union, Dict, Any

from sqlmodel import Session, select

from sqlmodel import Session, select
from fastapi import HTTPException, status # Import HTTPException and status

from app.models.client import ClientProfile, ClientProfileCreate, ClientProfileUpdate
from app.models.user import User, UserRole, UserCreate # Import UserCreate
from app.crud.user import create as create_user, get_by_email # Import user create/get functions


def get(session: Session, client_id: int) -> Optional[ClientProfile]:
    """
    Get a client profile by ID.

    Args:
        session: Database session
        client_id: Client profile ID

    Returns:
        Optional[ClientProfile]: Client profile if found, None otherwise
    """
    return session.get(ClientProfile, client_id)


def get_by_user_id(session: Session, user_id: int) -> Optional[ClientProfile]:
    """
    Get a client profile by user ID.

    Args:
        session: Database session
        user_id: User ID

    Returns:
        Optional[ClientProfile]: Client profile if found, None otherwise
    """
    return session.exec(
        select(ClientProfile).where(ClientProfile.user_id == user_id)
    ).first()


def get_multi(
    session: Session, *, skip: int = 0, limit: int = 100, active_only: bool = True
) -> List[ClientProfile]:
    """
    Get multiple client profiles.

    Args:
        session: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        active_only: If True, only return active client profiles

    Returns:
        List[ClientProfile]: List of client profiles
    """
    query = select(ClientProfile)

    if active_only:
        query = query.where(ClientProfile.is_active == True)

    return session.exec(query.offset(skip).limit(limit)).all()


def create(session: Session, *, obj_in: ClientProfileCreate) -> ClientProfile:
    """
    Create a new client user and their associated profile.

    Args:
        session: Database session
        obj_in: Client profile and user creation data

    Returns:
        ClientProfile: Created client profile

    Raises:
        HTTPException: If a user with the given email already exists.
    """
    # Check if user with this email already exists
    existing_user = get_by_email(session, email=obj_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )

    # 1. Create the User
    # Provide a default full_name if not given, using company name as fallback
    user_full_name = obj_in.full_name or obj_in.company_name
    user_in = UserCreate(
        email=obj_in.email,
        password=obj_in.password,
        full_name=user_full_name, # Use provided or fallback name
        role=UserRole.CLIENT, # Explicitly set role to CLIENT
        is_active=True # Default new clients to active
    )
    new_user = create_user(session=session, obj_in=user_in)

    # 2. Create the ClientProfile, linking to the new user
    # Use model_dump (Pydantic v2) instead of dict()
    profile_data = obj_in.model_dump(exclude={"email", "password", "full_name"})
    db_obj = ClientProfile(**profile_data, user_id=new_user.id)

    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    # Eager load the user relationship for the response if needed,
    # or rely on the ClientProfileRead schema
    session.refresh(new_user) # Ensure user data is fresh if accessed via db_obj.user
    return db_obj


def update(
    session: Session,
    *,
    db_obj: ClientProfile,
    obj_in: Union[ClientProfileUpdate, Dict[str, Any]]
) -> ClientProfile:
    """
    Update a client profile.

    Args:
        session: Database session
        db_obj: Client profile to update
        obj_in: Client profile update data

    Returns:
        ClientProfile: Updated client profile
    """
    if isinstance(obj_in, dict):
        update_data = obj_in
    else:
        # Use model_dump (Pydantic v2) instead of dict()
        update_data = obj_in.model_dump(exclude_unset=True)

    # Update client profile attributes
    for field, value in update_data.items():
        setattr(db_obj, field, value)

    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def delete(session: Session, *, client_id: int) -> Optional[ClientProfile]:
    """
    Delete a client profile.

    Args:
        session: Database session
        client_id: Client profile ID

    Returns:
        Optional[ClientProfile]: Deleted client profile if found, None otherwise
    """
    client = session.get(ClientProfile, client_id)
    if client:
        # Also delete the associated user? Or just deactivate?
        # For now, just deleting the profile. Consider user lifecycle.
        session.delete(client)
        session.commit()
    return client

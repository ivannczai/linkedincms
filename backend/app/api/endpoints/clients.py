"""
Client endpoints module.

This module contains endpoints for client profile management.
"""
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app import crud
from app.api.deps import get_current_admin_user, get_current_user, get_session
from app.models.client import ClientProfile, ClientProfileCreate, ClientProfileRead, ClientProfileUpdate
from app.models.user import User, UserRole

router = APIRouter()


@router.get("/", response_model=List[ClientProfileRead])
def read_clients(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
) -> Any:
    """
    Retrieve all client profiles.
    
    Only accessible by admin users.
    """
    clients = crud.get_clients(
        session, skip=skip, limit=limit, active_only=active_only
    )
    return clients


@router.post("/", response_model=ClientProfileRead)
def create_client(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user), # Ensure only admin can create
    client_in: ClientProfileCreate, # Use the updated schema with user details
) -> Any:
    """
    Create a new client user and their associated profile.
    
    Only accessible by admin users.
    """
    # The CRUD function now handles user creation and email checks
    try:
        client = crud.create_client(session=session, obj_in=client_in)
        # Eager load user data for the response model if necessary
        # Accessing client.user might trigger a lazy load if not handled in CRUD
        # or if the session is closed before serialization.
        # Let's assume ClientProfileRead doesn't need deep user details beyond user_id
        return client
    except HTTPException as e:
        # Re-raise HTTPExceptions (like email exists) from CRUD
        raise e
    except ValueError as e: # Catch potential ValueErrors from CRUD if any remain
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        # Catch unexpected errors
        print(f"Unexpected error creating client: {e}") # Log for debugging
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/{client_id}", response_model=ClientProfileRead)
def read_client(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    client_id: int,
) -> Any:
    """
    Get a specific client profile by ID.
    
    Accessible by:
    - Admin users (can access any client profile)
    - Client users (can only access their own client profile)
    """
    client = crud.get_client(session, client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client profile not found",
        )
    
    # Check permissions
    if current_user.role != UserRole.ADMIN and client.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    return client


@router.put("/{client_id}", response_model=ClientProfileRead)
def update_client(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
    client_id: int,
    client_in: ClientProfileUpdate,
) -> Any:
    """
    Update a client profile.
    
    Only accessible by admin users.
    """
    client = crud.get_client(session, client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client profile not found",
        )
    
    client = crud.update_client(session, db_obj=client, obj_in=client_in)
    return client


@router.delete("/{client_id}", response_model=ClientProfileRead)
def delete_client(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
    client_id: int,
) -> Any:
    """
    Delete a client profile.
    
    Only accessible by admin users.
    """
    client = crud.get_client(session, client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client profile not found",
        )
    
    client = crud.delete_client(session, client_id=client_id)
    return client


@router.get("/me/", response_model=ClientProfileRead)
def read_client_me(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get the client profile of the current user.
    
    Only accessible by client users.
    """
    # Check if user is a client
    if current_user.role != UserRole.CLIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a client user",
        )
    
    # Get client profile
    client = crud.get_by_user_id(session, current_user.id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client profile not found",
        )
    
    return client

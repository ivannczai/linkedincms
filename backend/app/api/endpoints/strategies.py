"""
Strategy endpoints module.

This module contains endpoints for strategy management.
"""
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app import crud
from app.api.deps import get_current_admin_user, get_current_user, get_session
from app.models.strategy import Strategy, StrategyCreate, StrategyRead, StrategyUpdate
from app.models.user import User, UserRole

router = APIRouter()


@router.get("/", response_model=List[StrategyRead])
def read_strategies(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
) -> Any:
    """
    Retrieve all strategies.
    
    Only accessible by admin users.
    """
    strategies = crud.get_strategies(
        session, skip=skip, limit=limit, active_only=active_only
    )
    return strategies


@router.post("/", response_model=StrategyRead)
def create_strategy(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
    strategy_in: StrategyCreate,
) -> Any:
    """
    Create a new strategy.
    
    Only accessible by admin users.
    """
    # Check if client exists
    client = crud.get_client(session, strategy_in.client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client with ID {strategy_in.client_id} not found",
        )
    
    # Check if strategy already exists for this client
    existing_strategy = crud.get_by_client_id(session, strategy_in.client_id)
    if existing_strategy:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Strategy already exists for client with ID {strategy_in.client_id}",
        )
    
    # Create strategy
    strategy = crud.create_strategy(session, obj_in=strategy_in, check_client=False)
    return strategy


@router.get("/{strategy_id}", response_model=StrategyRead)
def read_strategy(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    strategy_id: int,
) -> Any:
    """
    Get a specific strategy by ID.
    
    Accessible by:
    - Admin users (can access any strategy)
    - Client users (can only access their own client's strategy)
    """
    strategy = crud.get_strategy(session, strategy_id)
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found",
        )
    
    # Check permissions for client users
    if current_user.role == UserRole.CLIENT:
        # Get client profile for the current user
        client = crud.get_by_user_id(session, current_user.id)
        if not client or strategy.client_id != client.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
    
    return strategy


@router.get("/client/{client_id}", response_model=StrategyRead)
def read_strategy_by_client(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    client_id: int,
) -> Any:
    """
    Get a strategy by client ID.
    
    Accessible by:
    - Admin users (can access any strategy)
    - Client users (can only access their own client's strategy)
    """
    # Check permissions for client users
    if current_user.role == UserRole.CLIENT:
        # Get client profile for the current user
        client = crud.get_by_user_id(session, current_user.id)
        if not client or client.id != client_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
    else:
        # For admin users, check if client exists
        client = crud.get_client(session, client_id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Client with ID {client_id} not found",
            )
    
    # Get strategy
    strategy = crud.get_by_client_id(session, client_id)
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy not found for client with ID {client_id}",
        )
    
    return strategy


@router.put("/{strategy_id}", response_model=StrategyRead)
def update_strategy(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
    strategy_id: int,
    strategy_in: StrategyUpdate,
) -> Any:
    """
    Update a strategy.
    
    Only accessible by admin users.
    """
    strategy = crud.get_strategy(session, strategy_id)
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found",
        )
    
    strategy = crud.update_strategy(session, db_obj=strategy, obj_in=strategy_in)
    return strategy


@router.delete("/{strategy_id}", response_model=StrategyRead)
def delete_strategy(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
    strategy_id: int,
) -> Any:
    """
    Delete a strategy.
    
    Only accessible by admin users.
    """
    strategy = crud.get_strategy(session, strategy_id)
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found",
        )
    
    strategy = crud.delete_strategy(session, strategy_id=strategy_id)
    return strategy


@router.get("/me/", response_model=StrategyRead)
def read_my_strategy(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get the strategy for the current user's client.
    
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
    
    # Get strategy
    strategy = crud.get_by_client_id(session, client.id)
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found for your client profile",
        )
    
    return strategy

"""
Strategy CRUD operations module.

This module contains CRUD operations for the Strategy model.
"""
from typing import List, Optional, Union, Dict, Any
import bleach # Import bleach

from sqlmodel import Session, select

from app.models.strategy import Strategy, StrategyCreate, StrategyUpdate
from app.models.client import ClientProfile

# --- Bleach Configuration (Copied from crud/content.py for consistency) ---
ALLOWED_TAGS = [
    'p', 'br', 'b', 'strong', 'i', 'em', 'ul', 'ol', 'li', 'a'
]
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target'], # Allow standard link attributes
}
# --------------------------

def sanitize_html(html_content: Optional[str]) -> Optional[str]:
    """Sanitizes HTML content using bleach."""
    if html_content is None:
        return None
    return bleach.clean(
        html_content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True # Remove disallowed tags completely
    )


def get(session: Session, strategy_id: int) -> Optional[Strategy]:
    """
    Get a strategy by ID.

    Args:
        session: Database session
        strategy_id: Strategy ID

    Returns:
        Optional[Strategy]: Strategy if found, None otherwise
    """
    return session.get(Strategy, strategy_id)


def get_by_client_id(session: Session, client_id: int) -> Optional[Strategy]:
    """
    Get a strategy by client ID.

    Args:
        session: Database session
        client_id: Client profile ID

    Returns:
        Optional[Strategy]: Strategy if found, None otherwise
    """
    return session.exec(
        select(Strategy).where(Strategy.client_id == client_id)
    ).first()


def get_multi(
    session: Session, *, skip: int = 0, limit: int = 100, active_only: bool = True
) -> List[Strategy]:
    """
    Get multiple strategies.

    Args:
        session: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        active_only: If True, only return active strategies

    Returns:
        List[Strategy]: List of strategies
    """
    query = select(Strategy)

    if active_only:
        query = query.where(Strategy.is_active == True)

    return session.exec(query.offset(skip).limit(limit)).all()


def create(
    session: Session, *, obj_in: StrategyCreate, check_client: bool = True
) -> Strategy:
    """
    Create a new strategy, sanitizing HTML details.

    Args:
        session: Database session
        obj_in: Strategy creation data
        check_client: If True, check that the client exists

    Returns:
        Strategy: Created strategy

    Raises:
        ValueError: If the client does not exist
    """
    # Check if client exists
    if check_client:
        client = session.get(ClientProfile, obj_in.client_id)
        if not client:
            raise ValueError(f"Client with ID {obj_in.client_id} not found")

    # Sanitize HTML details before creating the object
    sanitized_details = sanitize_html(obj_in.details)

    # Create a dictionary from the input object to modify it
    obj_in_data = obj_in.dict()
    obj_in_data['details'] = sanitized_details # Use sanitized details

    # Create strategy using the modified dictionary
    db_obj = Strategy(**obj_in_data)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update(
    session: Session,
    *,
    db_obj: Strategy,
    obj_in: Union[StrategyUpdate, Dict[str, Any]]
) -> Strategy:
    """
    Update a strategy, sanitizing HTML details if provided.

    Args:
        session: Database session
        db_obj: Strategy to update
        obj_in: Strategy update data

    Returns:
        Strategy: Updated strategy
    """
    if isinstance(obj_in, dict):
        update_data = obj_in
    else:
        update_data = obj_in.dict(exclude_unset=True)

    # Sanitize details if it's being updated
    if 'details' in update_data:
        update_data['details'] = sanitize_html(update_data['details'])

    # Update strategy attributes
    for field, value in update_data.items():
        setattr(db_obj, field, value)

    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def delete(session: Session, *, strategy_id: int) -> Optional[Strategy]:
    """
    Delete a strategy.

    Args:
        session: Database session
        strategy_id: Strategy ID

    Returns:
        Optional[Strategy]: Deleted strategy if found, None otherwise
    """
    strategy = session.get(Strategy, strategy_id)
    if strategy:
        session.delete(strategy)
        session.commit()
    return strategy

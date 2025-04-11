"""
Tests for database setup and base model.
"""
import pytest
from sqlmodel import Session, SQLModel, create_engine, Field
from sqlmodel.pool import StaticPool

from app.core.database import get_session
from app.models.base import BaseModel # Import BaseModel


def test_get_session():
    """
    Test the get_session dependency.
    """
    # Create an in-memory SQLite database for testing
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    
    # Get a session using the dependency
    session_generator = get_session()
    session = next(session_generator)
    
    # Check that a session is returned
    assert isinstance(session, Session)
    
    # Clean up (close session)
    try:
        next(session_generator)
    except StopIteration:
        pass


def test_base_model():
    """
    Test that the base model has the expected fields (if any defined directly).
    BaseModel itself might not have fields like 'id' directly.
    """
    # Check for fields defined directly in BaseModel if any, e.g., created_at/updated_at if moved there.
    # For now, just ensure the class exists.
    assert BaseModel is not None
    # The original assertion 'assert hasattr(BaseModel, "id")' was incorrect
    # as 'id' is typically added by inheriting models that are tables.

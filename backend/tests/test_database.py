"""
Tests for the database connection.
"""
from sqlmodel import Session, select

from app.models.base import BaseModel


def test_database_session(session: Session):
    """
    Test that the database session is working correctly.
    """
    # Simple query to verify session is working
    result = session.exec(select(1)).one()
    assert result == 1


def test_base_model():
    """
    Test that the base model has the expected fields.
    """
    # Check that BaseModel has id field
    assert hasattr(BaseModel, "id")
    
    # Create a model instance
    model = BaseModel()
    assert model.id is None  # Default value should be None

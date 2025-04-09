"""
Pytest configuration file.

This file contains fixtures and configuration for pytest.
"""
import os
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.main import app
from app.core.database import get_session


@pytest.fixture(name="client")
def client_fixture():
    """
    Create a FastAPI TestClient for testing API endpoints.
    
    Returns:
        TestClient: A FastAPI test client
    """
    yield TestClient(app)


@pytest.fixture(name="session")
def session_fixture():
    """
    Create an in-memory SQLite database session for testing.
    
    This fixture creates a new in-memory database for each test,
    ensuring test isolation.
    
    Returns:
        Session: A SQLModel session connected to an in-memory database
    """
    # Create an in-memory SQLite database for testing
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        # Override the get_session dependency
        def get_session_override():
            yield session
            
        app.dependency_overrides[get_session] = get_session_override
        
        yield session
    
    # Remove the override after the test
    app.dependency_overrides.clear()

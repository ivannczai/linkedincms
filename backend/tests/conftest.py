"""
Pytest configuration file.

This file contains fixtures and configuration for pytest.
"""
import os
import pytest
from typing import Dict, Generator # Import Dict and Generator
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.main import app
from app.core.database import get_session
from app.models.user import User, UserCreate, UserRole # Import User models
from app.crud.user import create as create_user # Import user CRUD
from app.core.security import get_password_hash # Import password hashing


@pytest.fixture(name="session")
def session_fixture() -> Generator[Session, None, None]: # Add type hint
    """
    Create an in-memory SQLite database session for testing.

    This fixture creates a new in-memory database for each test,
    ensuring test isolation.

    Yields:
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


@pytest.fixture(name="client")
def client_fixture(session: Session) -> TestClient: # Add session dependency
    """
    Create a FastAPI TestClient configured with the test session.

    Args:
        session: The test database session fixture.

    Returns:
        TestClient: A FastAPI test client.
    """
    # The session fixture already handles dependency override
    yield TestClient(app)


@pytest.fixture(name="normal_user_token_headers")
def normal_user_token_headers_fixture(client: TestClient, session: Session) -> Dict[str, str]:
    """
    Fixture to create a normal user and return their auth token headers.
    Uses a consistent email/password for potential reuse or retrieval.
    """
    email = "test@example.com"
    password = "password"
    # Check if user already exists (e.g., from another fixture/test)
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        user_in = UserCreate(
            email=email,
            password=password,
            full_name="Test User",
            role=UserRole.CLIENT, # Default to client or adjust as needed
            is_active=True
        )
        user = create_user(session=session, obj_in=user_in)

    # Login to get token
    login_data = {"username": email, "password": password}
    r = client.post("/api/v1/auth/token", data=login_data)
    assert r.status_code == 200, f"Failed to log in user {email}: {r.text}"
    tokens = r.json()
    a_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {a_token}"}
    return headers

# Add other fixtures if needed (e.g., admin_user_token_headers)
@pytest.fixture(name="admin_user_token_headers")
def admin_user_token_headers_fixture(client: TestClient, session: Session) -> Dict[str, str]:
    """
    Fixture to create an admin user and return their auth token headers.
    """
    email = "admin@example.com"
    password = "adminpassword"
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        user_in = UserCreate(
            email=email,
            password=password,
            full_name="Admin User",
            role=UserRole.ADMIN,
            is_active=True
        )
        user = create_user(session=session, obj_in=user_in)

    login_data = {"username": email, "password": password}
    r = client.post("/api/v1/auth/token", data=login_data)
    assert r.status_code == 200, f"Failed to log in admin user {email}: {r.text}"
    tokens = r.json()
    a_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {a_token}"}
    return headers

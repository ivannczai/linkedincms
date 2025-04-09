"""
Tests for authentication endpoints.
"""
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.security import get_password_hash
from app.models.user import User, UserRole


def test_login_success(client: TestClient, session: Session):
    """
    Test successful login.
    """
    # Create a test user
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Test User",
        role=UserRole.CLIENT,
    )
    session.add(user)
    session.commit()
    
    # Login
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "test@example.com", "password": "password123"},
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client: TestClient, session: Session):
    """
    Test login with invalid credentials.
    """
    # Create a test user
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Test User",
        role=UserRole.CLIENT,
    )
    session.add(user)
    session.commit()
    
    # Login with wrong password
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "test@example.com", "password": "wrongpassword"},
    )
    
    # Check response
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_login_inactive_user(client: TestClient, session: Session):
    """
    Test login with inactive user.
    """
    # Create an inactive test user
    user = User(
        email="inactive@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Inactive User",
        role=UserRole.CLIENT,
        is_active=False,
    )
    session.add(user)
    session.commit()
    
    # Login
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "inactive@example.com", "password": "password123"},
    )
    
    # Check response
    assert response.status_code == 400
    assert "Inactive user" in response.json()["detail"]


def test_test_token(client: TestClient, session: Session):
    """
    Test the test-token endpoint.
    """
    # Create a test user
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Test User",
        role=UserRole.CLIENT,
    )
    session.add(user)
    session.commit()
    
    # Login to get token
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "test@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]
    
    # Test token
    response = client.post(
        "/api/v1/auth/test-token",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["role"] == "client"
    assert "id" in data

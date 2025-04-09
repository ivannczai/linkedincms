"""
Tests for strategy API endpoints.
"""
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.security import get_password_hash
from app.crud.client import create as create_client
from app.crud.strategy import create as create_strategy
from app.models.client import ClientProfileCreate
from app.models.strategy import StrategyCreate
from app.models.user import User, UserRole


def test_create_strategy(client: TestClient, session: Session):
    """
    Test creating a strategy.
    """
    # Create an admin user
    admin_user = User(
        email="admin@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Admin User",
        role=UserRole.ADMIN,
    )
    session.add(admin_user)
    
    # Create a client user
    client_user = User(
        email="client@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Client User",
        role=UserRole.CLIENT,
    )
    session.add(client_user)
    session.commit()
    
    # Create client profile
    client_profile = create_client(
        session,
        obj_in=ClientProfileCreate(
            user_id=client_user.id,
            company_name="Test Company",
            industry="Technology",
        ),
    )
    
    # Login as admin
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "admin@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]
    
    # Create strategy
    response = client.post(
        "/api/v1/strategies/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "client_id": client_profile.id,
            "title": "Content Strategy 2025",
            "details": "# Content Strategy\n\nThis is a test strategy with Markdown content.",
        },
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Content Strategy 2025"
    assert data["client_id"] == client_profile.id


def test_create_strategy_not_admin(client: TestClient, session: Session):
    """
    Test creating a strategy as a non-admin user.
    """
    # Create a client user
    client_user = User(
        email="client@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Client User",
        role=UserRole.CLIENT,
    )
    session.add(client_user)
    session.commit()
    
    # Create client profile
    client_profile = create_client(
        session,
        obj_in=ClientProfileCreate(
            user_id=client_user.id,
            company_name="Test Company",
            industry="Technology",
        ),
    )
    
    # Login as client
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "client@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]
    
    # Try to create strategy
    response = client.post(
        "/api/v1/strategies/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "client_id": client_profile.id,
            "title": "Content Strategy 2025",
            "details": "# Content Strategy\n\nThis is a test strategy with Markdown content.",
        },
    )
    
    # Check response (should be forbidden)
    assert response.status_code == 403


def test_read_strategies(client: TestClient, session: Session):
    """
    Test reading all strategies.
    """
    # Create an admin user
    admin_user = User(
        email="admin@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Admin User",
        role=UserRole.ADMIN,
    )
    session.add(admin_user)
    
    # Create client users
    client_user1 = User(
        email="client1@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Client User 1",
        role=UserRole.CLIENT,
    )
    session.add(client_user1)
    
    client_user2 = User(
        email="client2@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Client User 2",
        role=UserRole.CLIENT,
    )
    session.add(client_user2)
    session.commit()
    
    # Create client profiles
    client_profile1 = create_client(
        session,
        obj_in=ClientProfileCreate(
            user_id=client_user1.id,
            company_name="Test Company 1",
            industry="Technology",
        ),
    )
    
    client_profile2 = create_client(
        session,
        obj_in=ClientProfileCreate(
            user_id=client_user2.id,
            company_name="Test Company 2",
            industry="Finance",
        ),
    )
    
    # Create strategies
    strategy1 = create_strategy(
        session,
        obj_in=StrategyCreate(
            client_id=client_profile1.id,
            title="Content Strategy 2025 - Tech",
            details="# Technology Content Strategy",
        ),
    )
    
    strategy2 = create_strategy(
        session,
        obj_in=StrategyCreate(
            client_id=client_profile2.id,
            title="Content Strategy 2025 - Finance",
            details="# Finance Content Strategy",
        ),
    )
    
    # Login as admin
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "admin@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]
    
    # Get all strategies
    response = client.get(
        "/api/v1/strategies/",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "Content Strategy 2025 - Tech"
    assert data[1]["title"] == "Content Strategy 2025 - Finance"


def test_read_strategy(client: TestClient, session: Session):
    """
    Test reading a specific strategy.
    """
    # Create an admin user
    admin_user = User(
        email="admin@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Admin User",
        role=UserRole.ADMIN,
    )
    session.add(admin_user)
    
    # Create a client user
    client_user = User(
        email="client@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Client User",
        role=UserRole.CLIENT,
    )
    session.add(client_user)
    session.commit()
    
    # Create client profile
    client_profile = create_client(
        session,
        obj_in=ClientProfileCreate(
            user_id=client_user.id,
            company_name="Test Company",
            industry="Technology",
        ),
    )
    
    # Create strategy
    strategy = create_strategy(
        session,
        obj_in=StrategyCreate(
            client_id=client_profile.id,
            title="Content Strategy 2025",
            details="# Content Strategy\n\nThis is a test strategy with Markdown content.",
        ),
    )
    
    # Login as admin
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "admin@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]
    
    # Get strategy
    response = client.get(
        f"/api/v1/strategies/{strategy.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Content Strategy 2025"
    assert data["client_id"] == client_profile.id


def test_read_strategy_by_client(client: TestClient, session: Session):
    """
    Test reading a strategy by client ID.
    """
    # Create an admin user
    admin_user = User(
        email="admin@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Admin User",
        role=UserRole.ADMIN,
    )
    session.add(admin_user)
    
    # Create a client user
    client_user = User(
        email="client@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Client User",
        role=UserRole.CLIENT,
    )
    session.add(client_user)
    session.commit()
    
    # Create client profile
    client_profile = create_client(
        session,
        obj_in=ClientProfileCreate(
            user_id=client_user.id,
            company_name="Test Company",
            industry="Technology",
        ),
    )
    
    # Create strategy
    strategy = create_strategy(
        session,
        obj_in=StrategyCreate(
            client_id=client_profile.id,
            title="Content Strategy 2025",
            details="# Content Strategy\n\nThis is a test strategy with Markdown content.",
        ),
    )
    
    # Login as admin
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "admin@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]
    
    # Get strategy by client ID
    response = client.get(
        f"/api/v1/strategies/client/{client_profile.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Content Strategy 2025"
    assert data["client_id"] == client_profile.id


def test_read_my_strategy(client: TestClient, session: Session):
    """
    Test reading the current user's client strategy.
    """
    # Create a client user
    client_user = User(
        email="client@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Client User",
        role=UserRole.CLIENT,
    )
    session.add(client_user)
    session.commit()
    
    # Create client profile
    client_profile = create_client(
        session,
        obj_in=ClientProfileCreate(
            user_id=client_user.id,
            company_name="Test Company",
            industry="Technology",
        ),
    )
    
    # Create strategy
    strategy = create_strategy(
        session,
        obj_in=StrategyCreate(
            client_id=client_profile.id,
            title="Content Strategy 2025",
            details="# Content Strategy\n\nThis is a test strategy with Markdown content.",
        ),
    )
    
    # Login as client
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "client@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]
    
    # Get own strategy
    response = client.get(
        "/api/v1/strategies/me/",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Content Strategy 2025"
    assert data["client_id"] == client_profile.id


def test_update_strategy(client: TestClient, session: Session):
    """
    Test updating a strategy.
    """
    # Create an admin user
    admin_user = User(
        email="admin@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Admin User",
        role=UserRole.ADMIN,
    )
    session.add(admin_user)
    
    # Create a client user
    client_user = User(
        email="client@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Client User",
        role=UserRole.CLIENT,
    )
    session.add(client_user)
    session.commit()
    
    # Create client profile
    client_profile = create_client(
        session,
        obj_in=ClientProfileCreate(
            user_id=client_user.id,
            company_name="Test Company",
            industry="Technology",
        ),
    )
    
    # Create strategy
    strategy = create_strategy(
        session,
        obj_in=StrategyCreate(
            client_id=client_profile.id,
            title="Content Strategy 2025",
            details="# Content Strategy\n\nThis is a test strategy with Markdown content.",
        ),
    )
    
    # Login as admin
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "admin@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]
    
    # Update strategy
    response = client.put(
        f"/api/v1/strategies/{strategy.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Updated Content Strategy 2025",
            "details": "# Updated Content Strategy\n\nThis is an updated test strategy.",
        },
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Content Strategy 2025"
    assert data["details"] == "# Updated Content Strategy\n\nThis is an updated test strategy."
    assert data["client_id"] == client_profile.id  # Should not change


def test_delete_strategy(client: TestClient, session: Session):
    """
    Test deleting a strategy.
    """
    # Create an admin user
    admin_user = User(
        email="admin@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Admin User",
        role=UserRole.ADMIN,
    )
    session.add(admin_user)
    
    # Create a client user
    client_user = User(
        email="client@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Client User",
        role=UserRole.CLIENT,
    )
    session.add(client_user)
    session.commit()
    
    # Create client profile
    client_profile = create_client(
        session,
        obj_in=ClientProfileCreate(
            user_id=client_user.id,
            company_name="Test Company",
            industry="Technology",
        ),
    )
    
    # Create strategy
    strategy = create_strategy(
        session,
        obj_in=StrategyCreate(
            client_id=client_profile.id,
            title="Content Strategy 2025",
            details="# Content Strategy\n\nThis is a test strategy with Markdown content.",
        ),
    )
    
    # Login as admin
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "admin@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]
    
    # Delete strategy
    response = client.delete(
        f"/api/v1/strategies/{strategy.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    # Check response
    assert response.status_code == 200
    
    # Check that strategy is deleted
    get_response = client.get(
        f"/api/v1/strategies/{strategy.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_response.status_code == 404

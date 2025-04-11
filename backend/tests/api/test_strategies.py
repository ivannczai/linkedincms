"""
Tests for strategy API endpoints.
"""
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.security import get_password_hash
from app.crud.client import create as create_client # Import create function
from app.crud.strategy import create as create_strategy
from app.models.client import ClientProfile, ClientProfileCreate # Import ClientProfile
from app.models.strategy import StrategyCreate
from app.models.user import User, UserRole


# Helper function to create a test client profile and user directly
def create_test_client_for_strategy(session: Session, email: str, password: str, company: str, industry: str, full_name: str = "Test Client Strategy") -> ClientProfile:
    client_in = ClientProfileCreate(
        email=email,
        password=password,
        full_name=full_name,
        company_name=company,
        industry=industry,
    )
    return create_client(session, obj_in=client_in)


def test_create_strategy(client: TestClient, session: Session):
    """
    Test creating a strategy.
    """
    # Create an admin user
    admin_user = User(
        email="admin_strat@example.com", # Unique email
        hashed_password=get_password_hash("password123"),
        full_name="Admin User Strat",
        role=UserRole.ADMIN,
    )
    session.add(admin_user)
    session.commit()

    # Create client profile using helper
    client_profile = create_test_client_for_strategy(
        session,
        email="client_strat_create@example.com",
        password="password123",
        company="Test Company Strat Create",
        industry="Tech Strat Create",
        full_name="Client Strat Create"
    )

    # Login as admin
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "admin_strat@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]

    # Create strategy
    strategy_data = {
        "client_id": client_profile.id,
        "title": "Content Strategy 2025",
        "details": "# Content Strategy\n\nThis is a test strategy with Markdown content.",
    }
    response = client.post(
        "/api/v1/strategies/",
        headers={"Authorization": f"Bearer {token}"},
        json=strategy_data,
    )

    # Check response
    assert response.status_code == 200 # Assuming 200 OK
    data = response.json()
    assert data["title"] == strategy_data["title"]
    assert data["client_id"] == client_profile.id


def test_create_strategy_not_admin(client: TestClient, session: Session):
    """
    Test creating a strategy as a non-admin user.
    """
    # Create client profile using helper
    client_profile = create_test_client_for_strategy(
        session,
        email="client_strat_forbidden@example.com",
        password="password123",
        company="Test Company Strat Forbidden",
        industry="Tech Strat Forbidden",
        full_name="Client Strat Forbidden"
    )

    # Login as client
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "client_strat_forbidden@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]

    # Try to create strategy
    strategy_data = {
        "client_id": client_profile.id,
        "title": "Forbidden Strategy",
        "details": "This should not be created.",
    }
    response = client.post(
        "/api/v1/strategies/",
        headers={"Authorization": f"Bearer {token}"},
        json=strategy_data,
    )

    # Check response (should be forbidden)
    assert response.status_code == 403


def test_read_strategies(client: TestClient, session: Session):
    """
    Test reading all strategies.
    """
    # Create an admin user
    admin_user = User(
        email="admin_strat_read@example.com", # Unique email
        hashed_password=get_password_hash("password123"),
        full_name="Admin User Strat Read",
        role=UserRole.ADMIN,
    )
    session.add(admin_user)
    session.commit()

    # Create client profiles using helper
    client_profile1 = create_test_client_for_strategy(
        session,
        email="client_strat_read1@example.com",
        password="password123",
        company="Test Company Strat Read 1",
        industry="Tech Strat Read 1",
        full_name="Client Strat Read 1"
    )
    client_profile2 = create_test_client_for_strategy(
        session,
        email="client_strat_read2@example.com",
        password="password123",
        company="Test Company Strat Read 2",
        industry="Finance Strat Read",
        full_name="Client Strat Read 2"
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
        data={"username": "admin_strat_read@example.com", "password": "password123"},
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
    assert len(data) >= 2 # Check at least 2 exist
    titles = [item["title"] for item in data]
    assert strategy1.title in titles
    assert strategy2.title in titles


def test_read_strategy(client: TestClient, session: Session):
    """
    Test reading a specific strategy.
    """
    # Create an admin user
    admin_user = User(
        email="admin_strat_read_one@example.com", # Unique email
        hashed_password=get_password_hash("password123"),
        full_name="Admin User Strat Read One",
        role=UserRole.ADMIN,
    )
    session.add(admin_user)
    session.commit()

    # Create client profile using helper
    client_profile = create_test_client_for_strategy(
        session,
        email="client_strat_read_one@example.com",
        password="password123",
        company="Test Company Strat Read One",
        industry="Tech Strat Read One",
        full_name="Client Strat Read One"
    )

    # Create strategy
    strategy = create_strategy(
        session,
        obj_in=StrategyCreate(
            client_id=client_profile.id,
            title="Content Strategy 2025 Read One",
            details="# Content Strategy Read One",
        ),
    )

    # Login as admin
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "admin_strat_read_one@example.com", "password": "password123"},
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
    assert data["title"] == strategy.title
    assert data["client_id"] == client_profile.id


def test_read_strategy_by_client(client: TestClient, session: Session):
    """
    Test reading a strategy by client ID.
    """
    # Create an admin user
    admin_user = User(
        email="admin_strat_read_by_client@example.com", # Unique email
        hashed_password=get_password_hash("password123"),
        full_name="Admin User Strat Read By Client",
        role=UserRole.ADMIN,
    )
    session.add(admin_user)
    session.commit()

    # Create client profile using helper
    client_profile = create_test_client_for_strategy(
        session,
        email="client_strat_read_by_client@example.com",
        password="password123",
        company="Test Company Strat Read By Client",
        industry="Tech Strat Read By Client",
        full_name="Client Strat Read By Client"
    )

    # Create strategy
    strategy = create_strategy(
        session,
        obj_in=StrategyCreate(
            client_id=client_profile.id,
            title="Content Strategy 2025 Read By Client",
            details="# Content Strategy Read By Client",
        ),
    )

    # Login as admin
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "admin_strat_read_by_client@example.com", "password": "password123"},
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
    assert data["title"] == strategy.title
    assert data["client_id"] == client_profile.id


def test_read_my_strategy(client: TestClient, session: Session):
    """
    Test reading the current user's client strategy.
    """
    # Create client profile using helper
    client_profile = create_test_client_for_strategy(
        session,
        email="client_strat_read_me@example.com",
        password="password123",
        company="Test Company Strat Read Me",
        industry="Tech Strat Read Me",
        full_name="Client Strat Read Me"
    )

    # Create strategy
    strategy = create_strategy(
        session,
        obj_in=StrategyCreate(
            client_id=client_profile.id,
            title="Content Strategy 2025 Read Me",
            details="# Content Strategy Read Me",
        ),
    )

    # Login as client
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "client_strat_read_me@example.com", "password": "password123"},
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
    assert data["title"] == strategy.title
    assert data["client_id"] == client_profile.id


def test_update_strategy(client: TestClient, session: Session):
    """
    Test updating a strategy.
    """
    # Create an admin user
    admin_user = User(
        email="admin_strat_update@example.com", # Unique email
        hashed_password=get_password_hash("password123"),
        full_name="Admin User Strat Update",
        role=UserRole.ADMIN,
    )
    session.add(admin_user)
    session.commit()

    # Create client profile using helper
    client_profile = create_test_client_for_strategy(
        session,
        email="client_strat_update@example.com",
        password="password123",
        company="Test Company Strat Update",
        industry="Tech Strat Update",
        full_name="Client Strat Update"
    )

    # Create strategy
    strategy = create_strategy(
        session,
        obj_in=StrategyCreate(
            client_id=client_profile.id,
            title="Content Strategy 2025 Update",
            details="# Content Strategy Update",
        ),
    )

    # Login as admin
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "admin_strat_update@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]

    # Update strategy
    update_data = {
        "title": "Updated Content Strategy 2025",
        "details": "# Updated Content Strategy\n\nThis is an updated test strategy.",
    }
    response = client.put(
        f"/api/v1/strategies/{strategy.id}",
        headers={"Authorization": f"Bearer {token}"},
        json=update_data,
    )

    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == update_data["title"]
    assert data["details"] == update_data["details"]
    assert data["client_id"] == client_profile.id


def test_delete_strategy(client: TestClient, session: Session):
    """
    Test deleting a strategy.
    """
    # Create an admin user
    admin_user = User(
        email="admin_strat_delete@example.com", # Unique email
        hashed_password=get_password_hash("password123"),
        full_name="Admin User Strat Delete",
        role=UserRole.ADMIN,
    )
    session.add(admin_user)
    session.commit()

    # Create client profile using helper
    client_profile = create_test_client_for_strategy(
        session,
        email="client_strat_delete@example.com",
        password="password123",
        company="Test Company Strat Delete",
        industry="Tech Strat Delete",
        full_name="Client Strat Delete"
    )

    # Create strategy
    strategy = create_strategy(
        session,
        obj_in=StrategyCreate(
            client_id=client_profile.id,
            title="Content Strategy 2025 Delete",
            details="# Content Strategy Delete",
        ),
    )
    strategy_id = strategy.id # Store ID

    # Login as admin
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "admin_strat_delete@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]

    # Delete strategy
    response = client.delete(
        f"/api/v1/strategies/{strategy_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Check response
    assert response.status_code == 200 # Endpoint returns 200 OK with deleted object

    # Check that strategy is deleted
    get_response = client.get(
        f"/api/v1/strategies/{strategy_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_response.status_code == 404

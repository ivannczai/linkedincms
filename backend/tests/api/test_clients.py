"""
Tests for client API endpoints.
"""
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.security import get_password_hash
from app.crud.client import create as create_client
from app.models.client import ClientProfileCreate
from app.models.user import User, UserRole


def test_create_client(client: TestClient, session: Session):
    """
    Test creating a client profile.
    """
    # Create an admin user
    admin_user = User(
        email="admin@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Admin User",
        role=UserRole.ADMIN,
    )
    session.add(admin_user)
    session.commit() # Commit admin user
    
    # Client user is now created via the endpoint
    
    # Login as admin
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "admin@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]
    
    # Create client profile
    response = client.post(
        "/api/v1/clients/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            # Provide user details instead of user_id
            "email": "newclient@example.com",
            "password": "newpassword123",
            "full_name": "New Client User",
            "company_name": "Test Company",
            "industry": "Technology",
            "website": "https://example.com",
            "linkedin_url": "https://linkedin.com/company/test",
            "description": "A test company",
        },
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["company_name"] == "Test Company"
    assert data["industry"] == "Technology"
    assert "user_id" in data # Check that a user_id was assigned
    # Optionally, query the DB to verify the user was created with correct details


def test_create_client_not_admin(client: TestClient, session: Session):
    """
    Test creating a client profile as a non-admin user.
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
    
    # Login as client
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "client@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]
    
    # Try to create client profile
    response = client.post(
        "/api/v1/clients/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "user_id": client_user.id,
            "company_name": "Test Company",
            "industry": "Technology",
        },
    )
    
    # Check response (should be forbidden)
    assert response.status_code == 403


def test_read_clients(client: TestClient, session: Session):
    """
    Test reading all client profiles.
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
    
    # Login as admin
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "admin@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]
    
    # Get all client profiles
    response = client.get(
        "/api/v1/clients/",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["company_name"] == "Test Company 1"
    assert data[1]["company_name"] == "Test Company 2"


def test_read_client(client: TestClient, session: Session):
    """
    Test reading a specific client profile.
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
    
    # Get client profile
    response = client.get(
        f"/api/v1/clients/{client_profile.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["company_name"] == "Test Company"
    assert data["industry"] == "Technology"
    assert data["user_id"] == client_user.id


def test_read_client_me(client: TestClient, session: Session):
    """
    Test reading the current user's client profile.
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
    
    # Get own client profile
    response = client.get(
        "/api/v1/clients/me/",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["company_name"] == "Test Company"
    assert data["industry"] == "Technology"
    assert data["user_id"] == client_user.id


def test_update_client(client: TestClient, session: Session):
    """
    Test updating a client profile.
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
    
    # Update client profile
    response = client.put(
        f"/api/v1/clients/{client_profile.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "company_name": "Updated Company",
            "website": "https://updated-example.com",
        },
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["company_name"] == "Updated Company"
    assert data["industry"] == "Technology"  # Should not change
    assert data["website"] == "https://updated-example.com"


def test_delete_client(client: TestClient, session: Session):
    """
    Test deleting a client profile.
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
    
    # Delete client profile
    response = client.delete(
        f"/api/v1/clients/{client_profile.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    # Check response
    assert response.status_code == 200
    
    # Check that client profile is deleted
    get_response = client.get(
        f"/api/v1/clients/{client_profile.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_response.status_code == 404

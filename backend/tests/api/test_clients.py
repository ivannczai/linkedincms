"""
Tests for client API endpoints.
"""
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.security import get_password_hash
from app.crud.client import create as create_client # Import create function
from app.models.client import ClientProfile, ClientProfileCreate # Import ClientProfile
from app.models.user import User, UserRole


# Helper function to create a test client profile and user directly
def create_test_client_via_crud(session: Session, email: str, password: str, company: str, industry: str, full_name: str = "Test Client") -> ClientProfile:
    client_in = ClientProfileCreate(
        email=email,
        password=password,
        full_name=full_name,
        company_name=company,
        industry=industry,
    )
    # Ensure the create function is imported correctly if needed, or handle potential errors
    try:
        return create_client(session, obj_in=client_in)
    except Exception as e:
        # If creation fails (e.g., duplicate email from another test), handle it
        print(f"Warning: Helper function failed to create client {email}: {e}")
        # Attempt to retrieve existing user/profile if creation failed due to duplicate
        user = session.exec(select(User).where(User.email == email)).first()
        if user and user.client_profile:
            return user.client_profile
        raise e # Re-raise if it wasn't a duplicate issue or retrieval failed


def test_create_client(client: TestClient, session: Session):
    """
    Test creating a client profile via the API endpoint.
    """
    # Create an admin user
    admin_user = User(
        email="admin_create@example.com", # Use unique email
        hashed_password=get_password_hash("password123"),
        full_name="Admin User",
        role=UserRole.ADMIN,
    )
    session.add(admin_user)
    session.commit() # Commit admin user

    # Login as admin
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "admin_create@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]

    # Create client profile via API
    client_data = {
        "email": "newclient_api@example.com",
        "password": "newpassword123",
        "full_name": "New Client User API", # Ensure full_name is provided
        "company_name": "Test Company API",
        "industry": "Technology API",
        "website": "https://example.com",
        "linkedin_url": "https://linkedin.com/company/test",
        "description": "A test company API",
    }
    response = client.post(
        "/api/v1/clients/",
        headers={"Authorization": f"Bearer {token}"},
        json=client_data,
    )

    # Check response
    assert response.status_code == 200 # Assuming 200 OK based on endpoint definition
    data = response.json()
    assert data["company_name"] == client_data["company_name"]
    assert data["industry"] == client_data["industry"]
    assert "user_id" in data


def test_create_client_not_admin(client: TestClient, session: Session):
    """
    Test creating a client profile as a non-admin user.
    """
    # Create a client user
    client_user = User(
        email="client_auth_test@example.com", # Unique email
        hashed_password=get_password_hash("password123"),
        full_name="Client User Auth",
        role=UserRole.CLIENT,
    )
    session.add(client_user)
    session.commit()

    # Login as client
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "client_auth_test@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]

    # Try to create client profile
    client_data = {
        "email": "anotherclient@example.com",
        "password": "password123",
        "full_name": "Another Client",
        "company_name": "Test Company Forbidden",
        "industry": "Technology Forbidden",
    }
    response = client.post(
        "/api/v1/clients/",
        headers={"Authorization": f"Bearer {token}"},
        json=client_data,
    )

    # Check response (should be forbidden)
    assert response.status_code == 403


def test_read_clients(client: TestClient, session: Session):
    """
    Test reading all client profiles.
    """
    # Create an admin user
    admin_user = User(
        email="admin_read@example.com", # Unique email
        hashed_password=get_password_hash("password123"),
        full_name="Admin User Read",
        role=UserRole.ADMIN,
    )
    session.add(admin_user)
    session.commit()

    # Create client profiles using helper
    client_profile1 = create_test_client_via_crud(
        session,
        email="client_read1@example.com",
        password="password123",
        company="Test Company Read 1",
        industry="Tech Read",
        full_name="Client Read 1"
    )
    client_profile2 = create_test_client_via_crud(
        session,
        email="client_read2@example.com",
        password="password123",
        company="Test Company Read 2",
        industry="Finance Read",
        full_name="Client Read 2"
    )

    # Login as admin
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "admin_read@example.com", "password": "password123"},
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
    # Note: Order might not be guaranteed, check for presence instead of index
    assert len(data) >= 2 # Check at least 2 exist
    company_names = [item["company_name"] for item in data]
    assert client_profile1.company_name in company_names
    assert client_profile2.company_name in company_names


def test_read_client(client: TestClient, session: Session):
    """
    Test reading a specific client profile.
    """
    # Create an admin user
    admin_user = User(
        email="admin_read_one@example.com", # Unique email
        hashed_password=get_password_hash("password123"),
        full_name="Admin User Read One",
        role=UserRole.ADMIN,
    )
    session.add(admin_user)
    session.commit()

    # Create client profile using helper
    client_profile = create_test_client_via_crud(
        session,
        email="client_read_one@example.com",
        password="password123",
        company="Test Company Read One",
        industry="Tech Read One",
        full_name="Client Read One"
    )

    # Login as admin
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "admin_read_one@example.com", "password": "password123"},
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
    assert data["company_name"] == client_profile.company_name
    assert data["industry"] == client_profile.industry
    assert data["user_id"] == client_profile.user_id


def test_read_client_me(client: TestClient, session: Session):
    """
    Test reading the current user's client profile.
    """
    # Create client profile using helper
    client_profile = create_test_client_via_crud(
        session,
        email="client_read_me@example.com",
        password="password123",
        company="Test Company Read Me",
        industry="Tech Read Me",
        full_name="Client Read Me"
    )

    # Login as client
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "client_read_me@example.com", "password": "password123"},
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
    assert data["company_name"] == client_profile.company_name
    assert data["industry"] == client_profile.industry
    assert data["user_id"] == client_profile.user_id


def test_update_client(client: TestClient, session: Session):
    """
    Test updating a client profile.
    """
    # Create an admin user
    admin_user = User(
        email="admin_update@example.com", # Unique email
        hashed_password=get_password_hash("password123"),
        full_name="Admin User Update",
        role=UserRole.ADMIN,
    )
    session.add(admin_user)
    session.commit()

    # Create client profile using helper
    client_profile = create_test_client_via_crud(
        session,
        email="client_update@example.com",
        password="password123",
        company="Test Company Update",
        industry="Tech Update",
        full_name="Client Update"
    )

    # Login as admin
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "admin_update@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]

    # Update client profile
    update_data = {
        "company_name": "Updated Company",
        "website": "https://updated-example.com",
    }
    response = client.put(
        f"/api/v1/clients/{client_profile.id}",
        headers={"Authorization": f"Bearer {token}"},
        json=update_data,
    )

    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["company_name"] == update_data["company_name"]
    assert data["industry"] == client_profile.industry # Should not change
    assert data["website"] == update_data["website"]


def test_delete_client(client: TestClient, session: Session):
    """
    Test deleting a client profile.
    """
    # Create an admin user
    admin_user = User(
        email="admin_delete@example.com", # Unique email
        hashed_password=get_password_hash("password123"),
        full_name="Admin User Delete",
        role=UserRole.ADMIN,
    )
    session.add(admin_user)
    session.commit()

    # Create client profile using helper
    client_profile = create_test_client_via_crud(
        session,
        email="client_delete@example.com",
        password="password123",
        company="Test Company Delete",
        industry="Tech Delete",
        full_name="Client Delete"
    )
    client_profile_id = client_profile.id # Store ID

    # Login as admin
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "admin_delete@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]

    # Delete client profile
    response = client.delete(
        f"/api/v1/clients/{client_profile_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Check response
    assert response.status_code == 200 # Endpoint returns 200 OK with deleted object

    # Check that client profile is deleted
    get_response = client.get(
        f"/api/v1/clients/{client_profile_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_response.status_code == 404

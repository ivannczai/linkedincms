"""
Tests for content API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session
from datetime import date

from app.core.security import get_password_hash
from app.crud.client import create as create_client_crud
from app.crud.content import create as create_content_crud, update_status
from app.models.client import ClientProfileCreate
from app.models.content import ContentPieceCreate, ContentPieceUpdate, ContentStatus
from app.models.user import User, UserRole


# Helper to create client and user
def create_test_client_with_user(session: Session, email: str, company: str) -> User:
    client_in = ClientProfileCreate(
        email=email,
        password="password123",
        full_name=f"User for {company}",
        company_name=company,
        industry="Testing",
    )
    client_profile = create_client_crud(session, obj_in=client_in)
    user = session.get(User, client_profile.user_id)
    return user

# Helper to get auth token
def get_auth_token(client: TestClient, email: str, password: str = "password123") -> str:
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": email, "password": password},
    )
    assert login_response.status_code == 200
    return login_response.json()["access_token"]


def test_create_content(client: TestClient, session: Session):
    """
    Test creating content as admin.
    """
    admin_user = User(email="admin.content@test.com", hashed_password=get_password_hash("pw"), role=UserRole.ADMIN)
    session.add(admin_user)
    session.commit()
    
    test_client = create_test_client_with_user(session, "client.content.create@test.com", "Content Create Co")
    
    token = get_auth_token(client, "admin.content@test.com", "pw")
    
    response = client.post(
        "/api/v1/contents/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "client_id": test_client.client_profile.id,
            "title": "API Create Test",
            "idea": "Idea",
            "angle": "Angle",
            "content_body": "Body",
            "due_date": date.today().replace(year=date.today().year + 1).isoformat()
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "API Create Test"
    assert data["client_id"] == test_client.client_profile.id
    assert data["status"] == ContentStatus.DRAFT


def test_read_contents_admin(client: TestClient, session: Session):
    """
    Test reading all contents as admin.
    """
    admin_user = User(email="admin.content.read@test.com", hashed_password=get_password_hash("pw"), role=UserRole.ADMIN)
    session.add(admin_user)
    session.commit()
    
    client1 = create_test_client_with_user(session, "c1.content.read@test.com", "Read Co 1")
    client2 = create_test_client_with_user(session, "c2.content.read@test.com", "Read Co 2")
    create_content_crud(session, obj_in=ContentPieceCreate(client_id=client1.client_profile.id, title="C1 Read", idea="i", angle="a", content_body="b"))
    create_content_crud(session, obj_in=ContentPieceCreate(client_id=client2.client_profile.id, title="C2 Read", idea="i", angle="a", content_body="b"))

    token = get_auth_token(client, "admin.content.read@test.com", "pw")
    response = client.get("/api/v1/contents/", headers={"Authorization": f"Bearer {token}"})
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2 # Check at least the two created exist


def test_read_contents_client(client: TestClient, session: Session):
    """
    Test reading own contents as client.
    """
    client1_user = create_test_client_with_user(session, "c1.content.read.client@test.com", "Read Client Co 1")
    client2_user = create_test_client_with_user(session, "c2.content.read.client@test.com", "Read Client Co 2")
    
    content1 = create_content_crud(session, obj_in=ContentPieceCreate(client_id=client1_user.client_profile.id, title="C1 Client Read", idea="i", angle="a", content_body="b"))
    content2 = create_content_crud(session, obj_in=ContentPieceCreate(client_id=client2_user.client_profile.id, title="C2 Client Read", idea="i", angle="a", content_body="b"))

    token = get_auth_token(client, "c1.content.read.client@test.com")
    response = client.get("/api/v1/contents/", headers={"Authorization": f"Bearer {token}"})
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1 # Should only get own content
    assert data[0]["id"] == content1.id
    assert data[0]["title"] == "C1 Client Read"


def test_read_content_client_permission(client: TestClient, session: Session):
    """
    Test client cannot read another client's content directly by ID.
    """
    client1_user = create_test_client_with_user(session, "c1.content.perm@test.com", "Perm Co 1")
    client2_user = create_test_client_with_user(session, "c2.content.perm@test.com", "Perm Co 2")
    
    content2 = create_content_crud(session, obj_in=ContentPieceCreate(client_id=client2_user.client_profile.id, title="C2 Perm Read", idea="i", angle="a", content_body="b"))

    token = get_auth_token(client, "c1.content.perm@test.com")
    response = client.get(f"/api/v1/contents/{content2.id}", headers={"Authorization": f"Bearer {token}"})
    
    assert response.status_code == 403 # Forbidden


def test_approve_content(client: TestClient, session: Session):
    """
    Test client approving content.
    """
    client_user = create_test_client_with_user(session, "client.approve@test.com", "Approve Co")
    content = create_content_crud(session, obj_in=ContentPieceCreate(client_id=client_user.client_profile.id, title="Approve Me", idea="i", angle="a", content_body="b"))
    
    # Set status to PENDING_APPROVAL first (simulate admin submit)
    update_status(session, content_id=content.id, new_status=ContentStatus.PENDING_APPROVAL)

    token = get_auth_token(client, "client.approve@test.com")
    response = client.post(f"/api/v1/contents/{content.id}/approve", headers={"Authorization": f"Bearer {token}"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == ContentStatus.APPROVED


def test_request_revision(client: TestClient, session: Session):
    """
    Test client requesting revision.
    """
    client_user = create_test_client_with_user(session, "client.revision@test.com", "Revision Co")
    content = create_content_crud(session, obj_in=ContentPieceCreate(client_id=client_user.client_profile.id, title="Revise Me", idea="i", angle="a", content_body="b"))
    
    update_status(session, content_id=content.id, new_status=ContentStatus.PENDING_APPROVAL)

    token = get_auth_token(client, "client.revision@test.com")
    comment = "Needs more cowbell"
    response = client.post(
        f"/api/v1/contents/{content.id}/request-revision", 
        headers={"Authorization": f"Bearer {token}"},
        json={"review_comment": comment} # Send comment in body
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == ContentStatus.REVISION_REQUESTED
    assert data["review_comment"] == comment


def test_mark_as_posted(client: TestClient, session: Session):
    """
    Test client marking content as posted.
    """
    client_user = create_test_client_with_user(session, "client.posted@test.com", "Posted Co")
    content = create_content_crud(session, obj_in=ContentPieceCreate(client_id=client_user.client_profile.id, title="Post Me", idea="i", angle="a", content_body="b"))
    
    # Must be approved first
    update_status(session, content_id=content.id, new_status=ContentStatus.APPROVED)

    token = get_auth_token(client, "client.posted@test.com")
    response = client.post(f"/api/v1/contents/{content.id}/mark-as-posted", headers={"Authorization": f"Bearer {token}"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["published_at"] is not None
    # Status might remain APPROVED or change to PUBLISHED depending on exact logic in CRUD
    # Let's assume mark_as_posted sets published_at but doesn't change status from APPROVED
    assert data["status"] == ContentStatus.APPROVED or data["status"] == ContentStatus.PUBLISHED


def test_rate_content_api(client: TestClient, session: Session):
    """
    Test client rating content via API.
    """
    client_user = create_test_client_with_user(session, "client.rate.api@test.com", "Rate API Co")
    content = create_content_crud(session, obj_in=ContentPieceCreate(client_id=client_user.client_profile.id, title="Rate Me API", idea="i", angle="a", content_body="b"))
    
    # Approve content first
    update_status(session, content_id=content.id, new_status=ContentStatus.APPROVED)

    token = get_auth_token(client, "client.rate.api@test.com")
    
    # Test valid rating
    rating_payload = {"rating": 3.5}
    response = client.post(
        f"/api/v1/contents/{content.id}/rate", 
        headers={"Authorization": f"Bearer {token}"},
        json=rating_payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["client_rating"] == 3.5

    # Test invalid rating (wrong step)
    invalid_rating_payload = {"rating": 3.7}
    response = client.post(
        f"/api/v1/contents/{content.id}/rate", 
        headers={"Authorization": f"Bearer {token}"},
        json=invalid_rating_payload
    )
    assert response.status_code == 422 # Unprocessable Entity from Pydantic validation

    # Test rating before approval
    content_draft = create_content_crud(session, obj_in=ContentPieceCreate(client_id=client_user.client_profile.id, title="Rate Draft API", idea="i", angle="a", content_body="b"))
    response = client.post(
        f"/api/v1/contents/{content_draft.id}/rate", 
        headers={"Authorization": f"Bearer {token}"},
        json=rating_payload
    )
    assert response.status_code == 400 # Bad Request from CRUD check

    # Test non-client user trying to rate
    admin_user = User(email="admin.rate.api@test.com", hashed_password=get_password_hash("pw"), role=UserRole.ADMIN)
    session.add(admin_user)
    session.commit()
    admin_token = get_auth_token(client, "admin.rate.api@test.com", "pw")
    response = client.post(
        f"/api/v1/contents/{content.id}/rate", 
        headers={"Authorization": f"Bearer {admin_token}"},
        json=rating_payload
    )
    assert response.status_code == 403 # Forbidden

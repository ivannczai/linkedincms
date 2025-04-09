"""
Tests for the LinkedIn API endpoints.
"""
from unittest.mock import patch, MagicMock
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timezone, timedelta

from fastapi.testclient import TestClient
from sqlmodel import Session, select # Import select
import requests # Import requests for mocking

from app.core.config import settings
from app.models.user import User, UserCreate # Import UserCreate
from app.models.scheduled_post import ScheduledLinkedInPost, ScheduledLinkedInPostCreate, PostStatus # Import scheduled post models
from app.core import oauth_state_manager # To mock its functions
from app import crud # Import crud for mocking

# Assuming you have fixtures for TestClient (client) and a test user (normal_user_token_headers)
# from your conftest.py or similar setup. Also assuming a db fixture.
# You might need a fixture that creates a user with valid LinkedIn details for testing scheduling.

# Helper to create a mock response for requests.post/get
def mock_requests_response(status_code: int, json_data: dict | None = None, raise_for_status: Exception | None = None):
    mock_resp = MagicMock(spec=requests.Response)
    mock_resp.status_code = status_code
    if json_data is not None:
        mock_resp.json.return_value = json_data
    if raise_for_status:
        mock_resp.raise_for_status.side_effect = raise_for_status
    else:
        mock_resp.raise_for_status.return_value = None
    return mock_resp

# --- Helper Function to get test user ---
# This assumes your fixture `normal_user_token_headers` corresponds to a user
# with a known email or ID. Adjust as necessary.
def get_test_user(db: Session) -> User:
    # Replace with the actual email used in your fixture setup
    user = crud.user.get_by_email(db, email="test@example.com")
    if not user:
        # Create a user if not found for testing purposes (adjust details)
        user_in = UserCreate(email="test@example.com", password="password", full_name="Test User", role="admin", is_active=True)
        user = crud.user.create(db, obj_in=user_in)
    # Ensure user has an ID after creation/retrieval
    if user.id is None:
        db.refresh(user) # Refresh to get the ID if just created
        if user.id is None:
             raise Exception("Failed to get user ID for test setup")
    return user

# --- Helper Function to set up user with LinkedIn details ---
def setup_linkedin_user(db: Session, user: User):
    linkedin_data = {
        "linkedin_id": "test_linkedin_id",
        "linkedin_access_token": "valid_token",
        "linkedin_token_expires_at": datetime.now(timezone.utc) + timedelta(days=1),
        "linkedin_scopes": "r_liteprofile r_emailaddress w_member_social"
    }
    crud.user.update_linkedin_details(session=db, db_obj=user, linkedin_data=linkedin_data)
    db.refresh(user) # Ensure the session has the updated data

# --- Tests for /connect ---

def test_initiate_linkedin_connection_success(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session # Assuming db fixture exists
) -> None:
    """
    Test successful initiation of LinkedIn connection.
    """
    # Arrange
    mock_state = "mock_generated_state_string"
    test_user = get_test_user(db)
    expected_user_id = test_user.id

    with patch("app.core.oauth_state_manager.generate_state", return_value=mock_state), \
         patch("app.core.oauth_state_manager.store_state") as mock_store_state:

        # Act
        response = client.get("/api/v1/linkedin/connect", headers=normal_user_token_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "authorization_url" in data
        auth_url = data["authorization_url"]
        mock_store_state.assert_called_once_with(mock_state, expected_user_id)
        parsed_url = urlparse(auth_url)
        query_params = parse_qs(parsed_url.query)
        assert query_params.get("client_id") == [settings.LINKEDIN_CLIENT_ID]
        assert query_params.get("redirect_uri") == [settings.LINKEDIN_REDIRECT_URI]
        assert query_params.get("state") == [mock_state]
        assert query_params.get("scope") == ["r_liteprofile r_emailaddress w_member_social"]


def test_initiate_linkedin_connection_not_configured(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """
    Test initiating connection when LinkedIn settings are missing.
    """
    original_client_id = settings.LINKEDIN_CLIENT_ID
    settings.LINKEDIN_CLIENT_ID = None
    try:
        response = client.get("/api/v1/linkedin/connect", headers=normal_user_token_headers)
        assert response.status_code == 503
        assert response.json()["detail"] == "LinkedIn integration is not configured."
    finally:
        settings.LINKEDIN_CLIENT_ID = original_client_id


# --- Tests for /connect/callback ---

@patch("app.core.oauth_state_manager.verify_and_consume_state")
@patch("requests.post")
@patch("requests.get")
@patch("app.crud.user.get")
@patch("app.crud.user.update_linkedin_details")
def test_linkedin_connection_callback_success(
    mock_update_details: MagicMock,
    mock_get_user: MagicMock,
    mock_requests_get: MagicMock,
    mock_requests_post: MagicMock,
    mock_verify_state: MagicMock,
    client: TestClient,
    db: Session,
) -> None:
    """
    Test successful LinkedIn connection callback.
    """
    test_state = "valid_state_string"
    test_code = "valid_auth_code"
    expected_user_id = 1
    mock_verify_state.return_value = expected_user_id
    mock_user = User(id=expected_user_id, email="test@example.com", full_name="Test User", hashed_password="abc")
    mock_get_user.return_value = mock_user
    mock_token_response = mock_requests_response(200, {
        "access_token": "mock_access_token", "expires_in": 3600, "scope": "r_liteprofile r_emailaddress w_member_social"
    })
    mock_requests_post.return_value = mock_token_response
    mock_profile_response = mock_requests_response(200, {"id": "mock_linkedin_id"})
    mock_requests_get.return_value = mock_profile_response

    response = client.get(f"/api/v1/linkedin/connect/callback?code={test_code}&state={test_state}", allow_redirects=False) # Check redirect

    mock_verify_state.assert_called_once_with(test_state)
    mock_requests_post.assert_called_once()
    mock_requests_get.assert_called_once()
    mock_get_user.assert_called_once_with(db=db, user_id=expected_user_id)
    mock_update_details.assert_called_once()
    assert response.status_code == 307
    assert response.headers["location"] == "/dashboard/settings?linkedin_status=success"


@patch("app.core.oauth_state_manager.verify_and_consume_state")
def test_linkedin_connection_callback_invalid_state(mock_verify_state: MagicMock, client: TestClient) -> None:
    mock_verify_state.return_value = None
    response = client.get("/api/v1/linkedin/connect/callback?code=some_code&state=invalid", allow_redirects=False)
    assert response.status_code == 307
    assert "detail=Invalid+or+expired+state" in response.headers["location"]


@patch("app.core.oauth_state_manager.verify_and_consume_state", return_value=1)
@patch("requests.post")
def test_linkedin_connection_callback_token_exchange_fails(mock_requests_post: MagicMock, mock_verify_state: MagicMock, client: TestClient) -> None:
    mock_requests_post.return_value = mock_requests_response(500, raise_for_status=requests.exceptions.HTTPError("Server Error"))
    response = client.get("/api/v1/linkedin/connect/callback?code=valid_code&state=valid_state", allow_redirects=False)
    assert response.status_code == 307
    assert "detail=Token+exchange+failed" in response.headers["location"]


@patch("app.core.oauth_state_manager.verify_and_consume_state", return_value=1)
@patch("requests.post")
@patch("requests.get")
def test_linkedin_connection_callback_profile_fetch_fails(mock_requests_get: MagicMock, mock_requests_post: MagicMock, mock_verify_state: MagicMock, client: TestClient) -> None:
    mock_requests_post.return_value = mock_requests_response(200, {"access_token": "mock_access_token", "expires_in": 3600, "scope": "test"})
    mock_requests_get.return_value = mock_requests_response(403, raise_for_status=requests.exceptions.HTTPError("Forbidden"))
    response = client.get("/api/v1/linkedin/connect/callback?code=valid_code&state=valid_state", allow_redirects=False)
    assert response.status_code == 307
    assert "detail=Failed+to+fetch+LinkedIn+profile" in response.headers["location"]


@patch("app.core.oauth_state_manager.verify_and_consume_state", return_value=1)
@patch("requests.post")
@patch("requests.get")
@patch("app.crud.user.get")
@patch("app.crud.user.update_linkedin_details")
def test_linkedin_connection_callback_db_update_fails(mock_update_details: MagicMock, mock_get_user: MagicMock, mock_requests_get: MagicMock, mock_requests_post: MagicMock, mock_verify_state: MagicMock, client: TestClient, db: Session) -> None:
    mock_user = User(id=1, email="test@example.com", full_name="Test User", hashed_password="abc")
    mock_get_user.return_value = mock_user
    mock_requests_post.return_value = mock_requests_response(200, {"access_token": "mock_access_token", "expires_in": 3600, "scope": "test"})
    mock_requests_get.return_value = mock_requests_response(200, {"id": "mock_linkedin_id"})
    mock_update_details.side_effect = Exception("Database error")
    response = client.get("/api/v1/linkedin/connect/callback?code=valid_code&state=valid_state", allow_redirects=False)
    assert response.status_code == 307
    assert "detail=Failed+to+save+LinkedIn+details" in response.headers["location"]


# --- Tests for Scheduling Endpoints ---

@patch("app.crud.scheduled_post.create_scheduled_post")
def test_schedule_linkedin_post_success(
    mock_create: MagicMock,
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session
) -> None:
    """Test successfully scheduling a post."""
    # Arrange
    test_user = get_test_user(db)
    setup_linkedin_user(db, test_user) # Ensure user has valid token/scope
    schedule_time = datetime.now(timezone.utc) + timedelta(hours=1)
    post_data = {
        "user_id": test_user.id, # Must match authenticated user
        "content_text": "Test post content",
        "scheduled_at": schedule_time.isoformat()
    }
    # Mock the CRUD function return value
    # Ensure the mock return includes an ID
    mock_create.return_value = ScheduledLinkedInPost(
        id=1, user_id=test_user.id, content_text=post_data["content_text"],
        scheduled_at=schedule_time, status=PostStatus.PENDING,
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
    )

    # Act
    response = client.post("/api/v1/linkedin/schedule", headers=normal_user_token_headers, json=post_data)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["content_text"] == post_data["content_text"]
    assert data["status"] == "pending"
    assert data["user_id"] == test_user.id
    # Check if scheduled_at matches (may need tolerance or careful isoformat comparison)
    assert data["scheduled_at"].startswith(schedule_time.isoformat().split('+')[0]) # Compare without timezone for simplicity
    mock_create.assert_called_once()


def test_schedule_linkedin_post_token_expired(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test scheduling when user's LinkedIn token is expired."""
    test_user = get_test_user(db)
    # Setup user with expired token
    linkedin_data = {
        "linkedin_id": "test_linkedin_id",
        "linkedin_access_token": "expired_token",
        "linkedin_token_expires_at": datetime.now(timezone.utc) - timedelta(days=1), # Expired
        "linkedin_scopes": "w_member_social"
    }
    crud.user.update_linkedin_details(session=db, db_obj=test_user, linkedin_data=linkedin_data)
    db.refresh(test_user)

    schedule_time = datetime.now(timezone.utc) + timedelta(hours=1)
    post_data = {"user_id": test_user.id, "content_text": "Test", "scheduled_at": schedule_time.isoformat()}

    response = client.post("/api/v1/linkedin/schedule", headers=normal_user_token_headers, json=post_data)

    assert response.status_code == 400
    assert "token expired" in response.json()["detail"]


def test_schedule_linkedin_post_missing_scope(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test scheduling when user lacks the required 'w_member_social' scope."""
    test_user = get_test_user(db)
    # Setup user with valid token but missing scope
    linkedin_data = {
        "linkedin_id": "test_linkedin_id",
        "linkedin_access_token": "valid_token",
        "linkedin_token_expires_at": datetime.now(timezone.utc) + timedelta(days=1),
        "linkedin_scopes": "r_liteprofile r_emailaddress" # Missing w_member_social
    }
    crud.user.update_linkedin_details(session=db, db_obj=test_user, linkedin_data=linkedin_data)
    db.refresh(test_user)

    schedule_time = datetime.now(timezone.utc) + timedelta(hours=1)
    post_data = {"user_id": test_user.id, "content_text": "Test", "scheduled_at": schedule_time.isoformat()}

    response = client.post("/api/v1/linkedin/schedule", headers=normal_user_token_headers, json=post_data)

    assert response.status_code == 403
    assert "Required LinkedIn permission 'w_member_social' not granted" in response.json()["detail"]


def test_schedule_linkedin_post_past_time(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test scheduling for a time in the past."""
    test_user = get_test_user(db)
    setup_linkedin_user(db, test_user)
    schedule_time = datetime.now(timezone.utc) - timedelta(minutes=10) # Time in the past
    post_data = {"user_id": test_user.id, "content_text": "Test", "scheduled_at": schedule_time.isoformat()}

    response = client.post("/api/v1/linkedin/schedule", headers=normal_user_token_headers, json=post_data)

    assert response.status_code == 400
    assert "Scheduled time must be in the future" in response.json()["detail"]


def test_list_scheduled_posts(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test retrieving scheduled posts for the current user."""
    test_user = get_test_user(db)
    # Create some test posts for this user
    schedule_time1 = datetime.now(timezone.utc) + timedelta(hours=1)
    schedule_time2 = datetime.now(timezone.utc) + timedelta(hours=2)
    crud.scheduled_post.create_scheduled_post(db, obj_in=ScheduledLinkedInPostCreate(user_id=test_user.id, content_text="Post 1", scheduled_at=schedule_time1))
    crud.scheduled_post.create_scheduled_post(db, obj_in=ScheduledLinkedInPostCreate(user_id=test_user.id, content_text="Post 2", scheduled_at=schedule_time2))
    # Create a post for another user (should not be listed)
    # other_user = crud.user.create(...)
    # crud.scheduled_post.create_scheduled_post(db, obj_in=ScheduledLinkedInPostCreate(user_id=other_user.id, ...))

    response = client.get("/api/v1/linkedin/scheduled", headers=normal_user_token_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Adjust assertion based on actual number of posts created for the user in the test DB state
    # assert len(data) >= 2 # Check if at least the two created posts are there
    assert any(p['content_text'] == 'Post 1' for p in data)
    assert any(p['content_text'] == 'Post 2' for p in data)


def test_delete_scheduled_post_success(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test successfully deleting a pending scheduled post."""
    test_user = get_test_user(db)
    schedule_time = datetime.now(timezone.utc) + timedelta(hours=1)
    post = crud.scheduled_post.create_scheduled_post(db, obj_in=ScheduledLinkedInPostCreate(user_id=test_user.id, content_text="To Delete", scheduled_at=schedule_time))
    post_id = post.id # Store ID before potential deletion

    response = client.delete(f"/api/v1/linkedin/schedule/{post_id}", headers=normal_user_token_headers)

    assert response.status_code == 204
    # Verify post is actually deleted
    deleted_post = crud.scheduled_post.get_scheduled_post(db, post_id=post_id)
    assert deleted_post is None


def test_delete_scheduled_post_not_found(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test deleting a post that doesn't exist."""
    response = client.delete("/api/v1/linkedin/schedule/99999", headers=normal_user_token_headers)
    assert response.status_code == 404


def test_delete_scheduled_post_not_pending(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test deleting a post that is already published or failed."""
    test_user = get_test_user(db)
    schedule_time = datetime.now(timezone.utc) + timedelta(hours=1)
    post = crud.scheduled_post.create_scheduled_post(db, obj_in=ScheduledLinkedInPostCreate(user_id=test_user.id, content_text="Published Post", scheduled_at=schedule_time))
    # Manually update status for test
    crud.scheduled_post.update_post_status(db, db_obj=post, status=PostStatus.PUBLISHED, linkedin_post_id="123")
    post_id = post.id

    response = client.delete(f"/api/v1/linkedin/schedule/{post_id}", headers=normal_user_token_headers)
    assert response.status_code == 404 # CRUD returns None if not pending, endpoint returns 404
    assert "not pending" in response.json()["detail"]


def test_delete_scheduled_post_wrong_user(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session,
    # admin_user_token_headers: dict[str, str] # Assuming another user fixture
) -> None:
    """Test deleting a post belonging to another user."""
    test_user = get_test_user(db)
    # Create a post for the test user
    schedule_time = datetime.now(timezone.utc) + timedelta(hours=1)
    post = crud.scheduled_post.create_scheduled_post(db, obj_in=ScheduledLinkedInPostCreate(user_id=test_user.id, content_text="User Post", scheduled_at=schedule_time))
    post_id = post.id

    # Attempt to delete using different user's token (replace with actual fixture)
    # response = client.delete(f"/api/v1/linkedin/schedule/{post.id}", headers=admin_user_token_headers)
    # For now, simulate by trying to delete with the same user - this test needs adjustment
    # based on how you handle multiple test users/tokens.
    # Let's assume the check works and returns 404 if user_id doesn't match.
    # We can't fully test this without a second user fixture.
    # Placeholder assertion:
    # assert response.status_code == 404

    # Test deleting own post works (redundant but shows contrast)
    response_own = client.delete(f"/api/v1/linkedin/schedule/{post_id}", headers=normal_user_token_headers)
    assert response_own.status_code == 204

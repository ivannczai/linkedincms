"""
Tests for the LinkedIn API endpoints.
"""
import time # Import time
from unittest.mock import patch, MagicMock
from urllib.parse import urlparse, parse_qs, quote_plus # Keep quote_plus if needed elsewhere, but parse_qs decodes
from datetime import datetime, timezone, timedelta

from fastapi.testclient import TestClient
from sqlmodel import Session, select # Import select
import requests # Import requests for mocking

from app.core.config import settings
from app.models.user import User, UserCreate # Import UserCreate
from app.models.scheduled_post import ScheduledLinkedInPost, ScheduledLinkedInPostCreate, PostStatus # Import scheduled post models
from app.core import oauth_state_manager # To mock its functions
from app import crud # Import crud for mocking
from app.core.security import encrypt_data # Import encrypt_data for checking mock call

# Assuming you have fixtures for TestClient (client) and a test user (normal_user_token_headers)
# from your conftest.py or similar setup. Also assuming a session fixture.

# Helper to create a mock response for requests.post/get
def mock_requests_response(status_code: int, json_data: dict | None = None, headers: dict | None = None, raise_for_status: Exception | None = None, text: str | None = None):
    mock_resp = MagicMock(spec=requests.Response)
    mock_resp.status_code = status_code
    mock_resp.headers = headers or {}
    mock_resp.text = text or ''
    if json_data is not None:
        mock_resp.json.return_value = json_data
    if raise_for_status:
        mock_resp.raise_for_status.side_effect = raise_for_status
        # Attach the mock response to the exception if it's an HTTPError
        if isinstance(raise_for_status, requests.exceptions.HTTPError):
             raise_for_status.response = mock_resp
    else:
        mock_resp.raise_for_status.return_value = None
    return mock_resp

# --- Helper Function to get test user ---
# This assumes your fixture `normal_user_token_headers` corresponds to a user
# with a known email or ID. Adjust as necessary.
def get_test_user(session: Session) -> User: # Use session fixture name
    # Replace with the actual email used in your fixture setup
    user = crud.user.get_by_email(session, email="test@example.com") # Use session
    if not user:
        # Create a user if not found for testing purposes (adjust details)
        user_in = UserCreate(email="test@example.com", password="password", full_name="Test User", role="admin", is_active=True)
        user = crud.user.create(session, obj_in=user_in) # Use session
    # Ensure user has an ID after creation/retrieval
    if user.id is None:
        session.refresh(user) # Use session
        if user.id is None:
             raise Exception("Failed to get user ID for test setup")
    return user

# --- Helper Function to set up user with LinkedIn details ---
def setup_linkedin_user(session: Session, user: User, expired: bool = False): # Use session fixture name
    expires_at = datetime.now(timezone.utc) + (timedelta(days=-1) if expired else timedelta(days=1))
    plain_token = "valid_token" if not expired else "expired_token"
    linkedin_data = {
        "linkedin_id": "test_linkedin_id",
        "linkedin_access_token": plain_token, # Store plain token temporarily
        "linkedin_token_expires_at": expires_at,
        "linkedin_scopes": "openid profile email w_member_social"
    }
    # Encrypt token before saving in test setup as well
    if linkedin_data["linkedin_access_token"]:
         # Use the actual function here for setup consistency
         linkedin_data["linkedin_access_token"] = encrypt_data(linkedin_data["linkedin_access_token"])

    crud.user.update_linkedin_details(session=session, db_obj=user, linkedin_data=linkedin_data) # Use session
    session.refresh(user) # Use session

# --- Tests for /connect ---
def test_initiate_linkedin_connection_success(
    client: TestClient, normal_user_token_headers: dict[str, str], session: Session # Use session fixture name
) -> None:
    """
    Test successful initiation of LinkedIn connection.
    """
    # Arrange
    mock_state = "mock_generated_state_string"
    test_user = get_test_user(session) # Use session
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
        assert query_params.get("scope") == ["openid profile email w_member_social"] # Updated scopes


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
    session: Session, # Use session fixture name
) -> None:
    """
    Test successful LinkedIn connection callback.
    """
    test_state = "valid_state_string"
    test_code = "valid_auth_code"
    expected_user_id = 1
    mock_access_token_plain = "mock_access_token"
    mock_verify_state.return_value = expected_user_id
    mock_user = User(id=expected_user_id, email="test@example.com", full_name="Test User", hashed_password="abc")
    mock_get_user.return_value = mock_user
    mock_token_response = mock_requests_response(200, {
        "access_token": mock_access_token_plain, "expires_in": 3600, "scope": "openid profile email w_member_social" # Updated scopes
    })
    mock_requests_post.return_value = mock_token_response
    mock_profile_response = mock_requests_response(200, {"sub": "mock_linkedin_id"}) # Use 'sub' field
    mock_requests_get.return_value = mock_profile_response

    response = client.get(f"/api/v1/linkedin/connect/callback?code={test_code}&state={test_state}", follow_redirects=False) # Use follow_redirects

    mock_verify_state.assert_called_once_with(test_state)
    mock_requests_post.assert_called_once()
    mock_requests_get.assert_called_once() # Check userinfo call
    call_args_get, call_kwargs_get = mock_requests_get.call_args
    assert call_args_get[0] == "https://api.linkedin.com/v2/userinfo" # Verify userinfo endpoint
    mock_get_user.assert_called_once_with(session=session, user_id=expected_user_id) # Use session

    # Check that the mocked update_linkedin_details was called with the correct plain text token
    # (The real function handles encryption)
    mock_update_details.assert_called_once()
    call_args, call_kwargs = mock_update_details.call_args
    passed_linkedin_data = call_kwargs['linkedin_data']
    assert passed_linkedin_data["linkedin_id"] == "mock_linkedin_id"
    # Verify the plain token was passed to the CRUD function
    assert passed_linkedin_data["linkedin_access_token"] == mock_access_token_plain
    assert passed_linkedin_data["linkedin_scopes"] == "openid profile email w_member_social"

    assert response.status_code == 307
    assert response.headers["location"] == f"{settings.FRONTEND_URL_BASE}/dashboard/settings?linkedin_status=success" # Use setting


@patch("app.core.oauth_state_manager.verify_and_consume_state")
def test_linkedin_connection_callback_invalid_state(mock_verify_state: MagicMock, client: TestClient) -> None:
    mock_verify_state.return_value = None
    response = client.get("/api/v1/linkedin/connect/callback?code=some_code&state=invalid", follow_redirects=False)
    assert response.status_code == 307
    # Parse the redirect URL and check the decoded detail parameter
    redirect_url = urlparse(response.headers["location"])
    query_params = parse_qs(redirect_url.query)
    assert query_params.get("linkedin_status") == ["error"]
    assert query_params.get("detail") == ["Invalid or expired state"]


@patch("app.core.oauth_state_manager.verify_and_consume_state", return_value=1)
@patch("requests.post")
def test_linkedin_connection_callback_token_exchange_fails(mock_requests_post: MagicMock, mock_verify_state: MagicMock, client: TestClient) -> None:
    error_message = "Server Error"
    # Ensure the mock response is attached to the exception
    http_error = requests.exceptions.HTTPError(error_message)
    http_error.response = mock_requests_response(500, text=error_message)
    mock_requests_post.return_value = mock_requests_response(500, raise_for_status=http_error, text=error_message)

    response = client.get("/api/v1/linkedin/connect/callback?code=valid_code&state=valid_state", follow_redirects=False)
    assert response.status_code == 307
    # Parse the redirect URL and check the decoded detail parameter
    redirect_url = urlparse(response.headers["location"])
    query_params = parse_qs(redirect_url.query)
    assert query_params.get("linkedin_status") == ["error"]
    # Check the specific error message passed in the redirect
    assert query_params.get("detail") == [f"Token exchange failed: {error_message}"]


@patch("app.core.oauth_state_manager.verify_and_consume_state", return_value=1)
@patch("requests.post")
@patch("requests.get")
def test_linkedin_connection_callback_profile_fetch_fails(mock_requests_get: MagicMock, mock_requests_post: MagicMock, mock_verify_state: MagicMock, client: TestClient) -> None:
    error_message = "Forbidden"
    mock_requests_post.return_value = mock_requests_response(200, {"access_token": "mock_access_token", "expires_in": 3600, "scope": "test"})
    # Ensure the mock response is attached to the exception
    http_error = requests.exceptions.HTTPError(error_message)
    http_error.response = mock_requests_response(403, text=error_message)
    mock_requests_get.return_value = mock_requests_response(403, raise_for_status=http_error, text=error_message)

    response = client.get("/api/v1/linkedin/connect/callback?code=valid_code&state=valid_state", follow_redirects=False)
    assert response.status_code == 307
    # Parse the redirect URL and check the decoded detail parameter
    redirect_url = urlparse(response.headers["location"])
    query_params = parse_qs(redirect_url.query)
    assert query_params.get("linkedin_status") == ["error"]
    # Check the specific error message passed in the redirect
    assert query_params.get("detail") == [f"Failed to fetch LinkedIn userinfo: {error_message}"]


@patch("app.core.oauth_state_manager.verify_and_consume_state", return_value=1)
@patch("requests.post")
@patch("requests.get")
@patch("app.crud.user.get")
@patch("app.crud.user.update_linkedin_details")
def test_linkedin_connection_callback_db_update_fails(mock_update_details: MagicMock, mock_get_user: MagicMock, mock_requests_get: MagicMock, mock_requests_post: MagicMock, mock_verify_state: MagicMock, client: TestClient, session: Session) -> None: # Use session fixture name
    error_message = "Database error"
    mock_user = User(id=1, email="test@example.com", full_name="Test User", hashed_password="abc")
    mock_get_user.return_value = mock_user
    mock_requests_post.return_value = mock_requests_response(200, {"access_token": "mock_access_token", "expires_in": 3600, "scope": "test"})
    mock_requests_get.return_value = mock_requests_response(200, {"sub": "mock_linkedin_id"}) # Use 'sub'
    mock_update_details.side_effect = Exception(error_message) # Simulate DB error

    response = client.get("/api/v1/linkedin/connect/callback?code=valid_code&state=valid_state", follow_redirects=False)
    assert response.status_code == 307
    # Parse the redirect URL and check the decoded detail parameter
    redirect_url = urlparse(response.headers["location"])
    query_params = parse_qs(redirect_url.query)
    assert query_params.get("linkedin_status") == ["error"]
    # Check the specific error message passed in the redirect
    assert query_params.get("detail") == [f"Failed to save LinkedIn details: {error_message}"]


# --- Tests for Scheduling Endpoints ---

@patch("app.crud.scheduled_post.create_scheduled_post")
def test_schedule_linkedin_post_success(
    mock_create: MagicMock,
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    session: Session # Use session fixture name
) -> None:
    """Test successfully scheduling a post."""
    test_user = get_test_user(session) # Use session
    setup_linkedin_user(session, test_user) # Use session
    schedule_time = datetime.now(timezone.utc) + timedelta(hours=1)
    post_data = {
        "user_id": test_user.id,
        "content_text": "Test post content",
        "scheduled_at": schedule_time.isoformat()
    }
    mock_create.return_value = ScheduledLinkedInPost(
        id=1, user_id=test_user.id, content_text=post_data["content_text"],
        scheduled_at=schedule_time, status=PostStatus.PENDING, retry_count=0, # Added retry_count
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
    )

    response = client.post("/api/v1/linkedin/schedule", headers=normal_user_token_headers, json=post_data)

    assert response.status_code == 201
    data = response.json()
    assert data["content_text"] == post_data["content_text"]
    assert data["status"] == "pending"
    assert data["user_id"] == test_user.id
    assert data["retry_count"] == 0 # Check retry_count
    assert data["scheduled_at"].startswith(schedule_time.isoformat().split('+')[0])
    mock_create.assert_called_once()


def test_schedule_linkedin_post_token_expired(
    client: TestClient, normal_user_token_headers: dict[str, str], session: Session # Use session fixture name
) -> None:
    """Test scheduling when user's LinkedIn token is expired."""
    test_user = get_test_user(session) # Use session
    setup_linkedin_user(session, test_user, expired=True) # Use session

    schedule_time = datetime.now(timezone.utc) + timedelta(hours=1)
    post_data = {"user_id": test_user.id, "content_text": "Test", "scheduled_at": schedule_time.isoformat()}

    response = client.post("/api/v1/linkedin/schedule", headers=normal_user_token_headers, json=post_data)

    assert response.status_code == 400
    assert "token expired" in response.json()["detail"]


def test_schedule_linkedin_post_missing_scope(
    client: TestClient, normal_user_token_headers: dict[str, str], session: Session # Use session fixture name
) -> None:
    """Test scheduling when user lacks the required 'w_member_social' scope."""
    test_user = get_test_user(session) # Use session
    # Setup user with valid token but missing scope
    linkedin_data = {
        "linkedin_id": "test_linkedin_id",
        "linkedin_access_token": "valid_token",
        "linkedin_token_expires_at": datetime.now(timezone.utc) + timedelta(days=1),
        "linkedin_scopes": "openid profile email" # Missing w_member_social
    }
    # Encrypt token
    from app.core.security import encrypt_data
    linkedin_data["linkedin_access_token"] = encrypt_data(linkedin_data["linkedin_access_token"])
    crud.user.update_linkedin_details(session=session, db_obj=test_user, linkedin_data=linkedin_data) # Use session
    session.refresh(test_user) # Use session

    schedule_time = datetime.now(timezone.utc) + timedelta(hours=1)
    post_data = {"user_id": test_user.id, "content_text": "Test", "scheduled_at": schedule_time.isoformat()}

    response = client.post("/api/v1/linkedin/schedule", headers=normal_user_token_headers, json=post_data)

    assert response.status_code == 403
    assert "Required LinkedIn permission 'w_member_social' not granted" in response.json()["detail"]


def test_schedule_linkedin_post_past_time(
    client: TestClient, normal_user_token_headers: dict[str, str], session: Session # Use session fixture name
) -> None:
    """Test scheduling for a time in the past."""
    test_user = get_test_user(session) # Use session
    setup_linkedin_user(session, test_user) # Use session
    schedule_time = datetime.now(timezone.utc) - timedelta(minutes=10) # Time in the past
    post_data = {"user_id": test_user.id, "content_text": "Test", "scheduled_at": schedule_time.isoformat()}

    response = client.post("/api/v1/linkedin/schedule", headers=normal_user_token_headers, json=post_data)

    assert response.status_code == 400
    assert "Scheduled time must be in the future" in response.json()["detail"]


def test_list_scheduled_posts(
    client: TestClient, normal_user_token_headers: dict[str, str], session: Session # Use session fixture name
) -> None:
    """Test retrieving scheduled posts for the current user."""
    test_user = get_test_user(session) # Use session
    # Clean up previous posts for this user to ensure count is correct
    existing_posts = crud.scheduled_post.get_scheduled_posts_by_user(session, user_id=test_user.id, limit=1000) # Use session
    for post in existing_posts:
        session.delete(post) # Use session
    session.commit() # Use session

    # Create some test posts for this user
    schedule_time1 = datetime.now(timezone.utc) + timedelta(hours=1)
    schedule_time2 = datetime.now(timezone.utc) + timedelta(hours=2)
    crud.scheduled_post.create_scheduled_post(session, obj_in=ScheduledLinkedInPostCreate(user_id=test_user.id, content_text="Post 1", scheduled_at=schedule_time1)) # Use session
    crud.scheduled_post.create_scheduled_post(session, obj_in=ScheduledLinkedInPostCreate(user_id=test_user.id, content_text="Post 2", scheduled_at=schedule_time2)) # Use session

    response = client.get("/api/v1/linkedin/scheduled", headers=normal_user_token_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2 # Only posts for the current user
    assert data[0]["content_text"] == "Post 2" # Assuming default order is desc
    assert data[1]["content_text"] == "Post 1"


def test_delete_scheduled_post_success(
    client: TestClient, normal_user_token_headers: dict[str, str], session: Session # Use session fixture name
) -> None:
    """Test successfully deleting a pending scheduled post."""
    test_user = get_test_user(session) # Use session
    schedule_time = datetime.now(timezone.utc) + timedelta(hours=1)
    post = crud.scheduled_post.create_scheduled_post(session, obj_in=ScheduledLinkedInPostCreate(user_id=test_user.id, content_text="To Delete", scheduled_at=schedule_time)) # Use session
    post_id = post.id # Store ID before potential deletion

    response = client.delete(f"/api/v1/linkedin/schedule/{post_id}", headers=normal_user_token_headers)

    assert response.status_code == 204
    # Verify post is actually deleted
    deleted_post = crud.scheduled_post.get_scheduled_post(session, post_id=post_id) # Use session
    assert deleted_post is None


def test_delete_scheduled_post_not_found(
    client: TestClient, normal_user_token_headers: dict[str, str], session: Session # Use session fixture name
) -> None:
    """Test deleting a post that doesn't exist."""
    response = client.delete("/api/v1/linkedin/schedule/99999", headers=normal_user_token_headers)
    assert response.status_code == 404


def test_delete_scheduled_post_not_pending(
    client: TestClient, normal_user_token_headers: dict[str, str], session: Session # Use session fixture name
) -> None:
    """Test deleting a post that is already published or failed."""
    test_user = get_test_user(session) # Use session
    schedule_time = datetime.now(timezone.utc) + timedelta(hours=1)
    post = crud.scheduled_post.create_scheduled_post(session, obj_in=ScheduledLinkedInPostCreate(user_id=test_user.id, content_text="Published Post", scheduled_at=schedule_time)) # Use session
    # Manually update status for test
    crud.scheduled_post.update_post_status(session, db_obj=post, status=PostStatus.PUBLISHED, linkedin_post_id="123") # Use session
    post_id = post.id

    response = client.delete(f"/api/v1/linkedin/schedule/{post_id}", headers=normal_user_token_headers)
    assert response.status_code == 404 # CRUD returns None if not pending, endpoint returns 404
    assert "not pending" in response.json()["detail"]


# --- Tests for Scheduler Job (More complex, might need separate setup) ---

@patch("app.core.security.decrypt_data") # Mock decryption for scheduler tests
@patch("requests.post")
@patch("app.crud.scheduled_post.update_post_status")
@patch("app.crud.scheduled_post.update_for_retry")
def test_scheduler_job_success(
    mock_update_retry: MagicMock,
    mock_update_status: MagicMock,
    mock_requests_post: MagicMock,
    mock_decrypt: MagicMock, # Add mock decrypt
    session: Session # Use session fixture name
):
    """Test the scheduler job successfully publishing a post."""
    # Arrange
    from app.main import publish_scheduled_linkedin_posts # Import the job function
    test_user = get_test_user(session) # Use session
    # Setup user with encrypted token
    setup_linkedin_user(session, test_user) # Use session
    # Mock decrypt_data to return the plain token
    mock_decrypt.return_value = "valid_token"

    schedule_time = datetime.now(timezone.utc) - timedelta(minutes=5) # Due now
    post = crud.scheduled_post.create_scheduled_post(session, obj_in=ScheduledLinkedInPostCreate(user_id=test_user.id, content_text="Publish Me", scheduled_at=schedule_time)) # Use session

    mock_requests_post.return_value = mock_requests_response(201, headers={"X-RestLi-Id": "linkedin-post-123"})

    # Act
    publish_scheduled_linkedin_posts() # Run the job function directly

    # Assert
    mock_decrypt.assert_called_once() # Ensure decryption was attempted
    mock_requests_post.assert_called_once() # Check LinkedIn API was called
    mock_update_status.assert_called_once() # Check status update was called
    args, kwargs = mock_update_status.call_args
    assert kwargs["status"] == PostStatus.PUBLISHED
    assert kwargs["linkedin_post_id"] == "linkedin-post-123"
    mock_update_retry.assert_not_called() # Ensure retry logic wasn't triggered


@patch("app.core.security.decrypt_data") # Mock decryption for scheduler tests
@patch("requests.post")
@patch("app.crud.scheduled_post.update_post_status")
@patch("app.crud.scheduled_post.update_for_retry")
def test_scheduler_job_retry_logic(
    mock_update_retry: MagicMock,
    mock_update_status: MagicMock,
    mock_requests_post: MagicMock,
    mock_decrypt: MagicMock, # Add mock decrypt
    session: Session # Use session fixture name
):
    """Test the scheduler job retrying on a transient error."""
    from app.main import publish_scheduled_linkedin_posts, MAX_RETRIES, RETRY_DELAY_MINUTES
    test_user = get_test_user(session) # Use session
    setup_linkedin_user(session, test_user) # Use session
    # Mock decrypt_data to return the plain token
    mock_decrypt.return_value = "valid_token"

    schedule_time = datetime.now(timezone.utc) - timedelta(minutes=5)
    post = crud.scheduled_post.create_scheduled_post(session, obj_in=ScheduledLinkedInPostCreate(user_id=test_user.id, content_text="Retry Me", scheduled_at=schedule_time)) # Use session

    # Simulate a retryable error (e.g., 500 server error)
    error_message = "Server Error"
    mock_requests_post.return_value = mock_requests_response(500, raise_for_status=requests.exceptions.HTTPError(error_message), text=error_message)

    # Act - First run (should trigger retry)
    publish_scheduled_linkedin_posts()

    # Assert - First run
    mock_decrypt.assert_called_once() # Decryption attempted
    mock_requests_post.assert_called_once()
    mock_update_retry.assert_called_once()
    mock_update_status.assert_not_called()
    args_retry, kwargs_retry = mock_update_retry.call_args
    assert kwargs_retry["db_obj"].retry_count == 1
    assert kwargs_retry["new_scheduled_at"] > schedule_time
    assert "API Error (Retry 1/3" in kwargs_retry["retry_error_message"]

    # Simulate time passing and run again (still failing)
    mock_decrypt.reset_mock() # Reset mock for next call count
    mock_requests_post.reset_mock()
    mock_update_retry.reset_mock()
    post.scheduled_at = datetime.now(timezone.utc) - timedelta(minutes=1) # Make it due again
    session.add(post); session.commit(); session.refresh(post) # Use session

    # Act - Second run
    publish_scheduled_linkedin_posts()

    # Assert - Second run
    mock_decrypt.assert_called_once() # Decryption attempted again
    mock_requests_post.assert_called_once()
    mock_update_retry.assert_called_once()
    mock_update_status.assert_not_called()
    args_retry, kwargs_retry = mock_update_retry.call_args
    assert kwargs_retry["db_obj"].retry_count == 2
    assert "API Error (Retry 2/3" in kwargs_retry["retry_error_message"]

    # Simulate time passing and run again (still failing, max retries)
    mock_decrypt.reset_mock()
    mock_requests_post.reset_mock()
    mock_update_retry.reset_mock()
    post.scheduled_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    session.add(post); session.commit(); session.refresh(post) # Use session

    # Act - Third run (should hit max retries and fail permanently)
    publish_scheduled_linkedin_posts()

    # Assert - Third run
    mock_decrypt.assert_called_once() # Decryption attempted again
    mock_requests_post.assert_called_once()
    mock_update_retry.assert_not_called() # Should not retry again
    mock_update_status.assert_called_once() # Should call update_post_status with FAILED
    args_status, kwargs_status = mock_update_status.call_args
    assert kwargs_status["status"] == PostStatus.FAILED
    assert "API Error: 500" in kwargs_status["error_message"] # Check for specific final error

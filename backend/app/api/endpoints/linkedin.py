"""
API endpoints for LinkedIn integration (OAuth connection and Scheduling).
"""
import logging # Import logging
from typing import Any, List # Import List
from urllib.parse import urlencode, quote # Import quote for encoding detail message
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, Query # Import Query
from fastapi.responses import RedirectResponse, JSONResponse
import requests # Import requests library
from sqlmodel import Session # Import Session

from app.api import deps
from app.core.config import settings # Import settings
from app.core import oauth_state_manager
from app.core.database import get_session # Import get_session directly
from app.models.user import User
# Import scheduled post models and crud
from app.models.scheduled_post import (
    ScheduledLinkedInPost,
    ScheduledLinkedInPostCreate,
    ScheduledLinkedInPostRead,
    PostStatus # Import PostStatus
)
# Import crud functions
from app import crud

# Get logger instance
logger = logging.getLogger(__name__)

router = APIRouter()

LINKEDIN_AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
LINKEDIN_API_BASE_URL = "https://api.linkedin.com/v2"
# Updated Scopes for OpenID Connect + Sharing
LINKEDIN_SCOPES = "openid profile email w_member_social"

# Define the frontend path for settings redirect
FRONTEND_SETTINGS_PATH = "/dashboard/settings"
# Define timeout for requests to LinkedIn API
LINKEDIN_API_TIMEOUT = 20 # Increased timeout to 20 seconds


@router.get("/connect", response_class=JSONResponse)
def initiate_linkedin_connection(
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Initiates the OAuth 2.0 flow to connect the user's LinkedIn account.

    Generates a state parameter, stores it, and returns the LinkedIn
    authorization URL for the frontend to redirect the user to.
    """
    if not settings.LINKEDIN_CLIENT_ID or not settings.LINKEDIN_REDIRECT_URI:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LinkedIn integration is not configured.",
        )

    state = oauth_state_manager.generate_state()
    # Assuming current_user.id is the integer primary key
    oauth_state_manager.store_state(state, current_user.id)

    params = {
        "response_type": "code",
        "client_id": settings.LINKEDIN_CLIENT_ID,
        "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
        "state": state,
        "scope": LINKEDIN_SCOPES, # Use updated scopes
    }
    authorization_url = f"{LINKEDIN_AUTH_URL}?{urlencode(params)}"

    # Return the URL in a JSON response for the frontend to handle the redirect
    return {"authorization_url": authorization_url}


@router.get("/connect/callback")
async def linkedin_connection_callback(
    request: Request,
    db: Session = Depends(get_session), # Corrected dependency
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
) -> RedirectResponse:
    """
    Handles the callback from LinkedIn after user authorization.

    Verifies state, exchanges code for token, fetches user info, updates
    the user record in the DB, and redirects back to the frontend.
    """
    # Construct the base redirect URL using the setting
    frontend_redirect_url = f"{settings.FRONTEND_URL_BASE}{FRONTEND_SETTINGS_PATH}"

    if error:
        # Redirect back to frontend with error status, properly encoding the description
        error_detail = quote(error_description or error or "Unknown error")
        logger.error(f"LinkedIn OAuth Error: {error} - {error_description}")
        redirect_url = f"{frontend_redirect_url}?linkedin_status=error&detail={error_detail}"
        return RedirectResponse(url=redirect_url)

    if not code or not state:
        # Redirect back to frontend with error status
        redirect_url = f"{frontend_redirect_url}?linkedin_status=error&detail=Missing code or state"
        return RedirectResponse(url=redirect_url)

    # 1. Verify state and get user ID
    user_id = oauth_state_manager.verify_and_consume_state(state)
    if user_id is None:
        # Redirect back to frontend with error status
        redirect_url = f"{frontend_redirect_url}?linkedin_status=error&detail=Invalid or expired state"
        return RedirectResponse(url=redirect_url)

    # Check if LinkedIn integration is configured
    if not all([settings.LINKEDIN_CLIENT_ID, settings.LINKEDIN_CLIENT_SECRET, settings.LINKEDIN_REDIRECT_URI]):
        redirect_url = f"{frontend_redirect_url}?linkedin_status=error&detail=LinkedIn integration not configured"
        return RedirectResponse(url=redirect_url)

    # 2. Exchange code for access token
    token_payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
        "client_id": settings.LINKEDIN_CLIENT_ID,
        "client_secret": settings.LINKEDIN_CLIENT_SECRET,
    }
    granted_scopes = None # Initialize granted_scopes
    try:
        response = requests.post(LINKEDIN_TOKEN_URL, data=token_payload, timeout=LINKEDIN_API_TIMEOUT) # Use timeout
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        token_data = response.json()
        access_token = token_data.get("access_token")
        expires_in = token_data.get("expires_in") # Seconds
        granted_scopes = token_data.get("scope") # Space-separated string OR COMMA-SEPARATED
        logger.info(f"Received scopes from LinkedIn token exchange: {granted_scopes}") # Log received scopes

        if not access_token or expires_in is None:
            raise ValueError("Missing access_token or expires_in in LinkedIn response")

        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    except requests.exceptions.RequestException as e:
        logger.error(f"LinkedIn token exchange failed: {e}", exc_info=True)
        error_detail = quote(f"Token exchange failed: {e}")
        redirect_url = f"{frontend_redirect_url}?linkedin_status=error&detail={error_detail}"
        return RedirectResponse(url=redirect_url)
    except ValueError as e:
        logger.error(f"Invalid token response from LinkedIn: {e}", exc_info=True)
        error_detail = quote(f"Invalid token response: {e}")
        redirect_url = f"{frontend_redirect_url}?linkedin_status=error&detail={error_detail}"
        return RedirectResponse(url=redirect_url)

    # 3. Fetch LinkedIn User Info (/v2/userinfo)
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        # Use the /userinfo endpoint provided by OpenID Connect
        userinfo_response = requests.get(f"{LINKEDIN_API_BASE_URL}/userinfo", headers=headers, timeout=LINKEDIN_API_TIMEOUT) # Use timeout
        userinfo_response.raise_for_status()
        userinfo_data = userinfo_response.json()
        # The user ID is in the 'sub' (subject) field for OpenID Connect
        linkedin_id = userinfo_data.get("sub")
        if not linkedin_id:
            raise ValueError("Could not retrieve LinkedIn user ID ('sub') from userinfo")
        # Optional: You could also retrieve name, email etc. from userinfo_data if needed later
        # linkedin_email = userinfo_data.get("email")
        # linkedin_name = userinfo_data.get("name")

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch LinkedIn userinfo: {e}", exc_info=True)
        error_detail = quote(f"Failed to fetch LinkedIn userinfo: {e}")
        redirect_url = f"{frontend_redirect_url}?linkedin_status=error&detail={error_detail}"
        return RedirectResponse(url=redirect_url)
    except ValueError as e:
        logger.error(f"Invalid userinfo response from LinkedIn: {e}", exc_info=True)
        error_detail = quote(f"Invalid userinfo response: {e}")
        redirect_url = f"{frontend_redirect_url}?linkedin_status=error&detail={error_detail}"
        return RedirectResponse(url=redirect_url)

    # 4. Update User record in DB
    try:
        # Corrected: Use 'session' instead of 'db' as keyword argument
        user_to_update = crud.user.get(session=db, user_id=user_id) # Get user by internal ID
        if not user_to_update:
            # Should not happen if state verification worked
            logger.error(f"User with ID {user_id} not found after state verification.")
            raise HTTPException(status_code=404, detail="User not found")

        linkedin_data = {
            "linkedin_id": linkedin_id, # Use the 'sub' field as the ID
            "linkedin_access_token": access_token, # Consider encrypting
            "linkedin_token_expires_at": expires_at, # This is timezone-aware (UTC)
            "linkedin_scopes": granted_scopes # Save the scopes received
        }
        logger.info(f"Attempting to save LinkedIn details for user {user_id}: Scopes='{granted_scopes}'") # Log scopes being saved
        crud.user.update_linkedin_details(session=db, db_obj=user_to_update, linkedin_data=linkedin_data)
        logger.info(f"Successfully saved LinkedIn details for user {user_id}")

    except Exception as e:
        logger.error(f"Error updating user {user_id} LinkedIn details in DB: {e}", exc_info=True)
        error_detail = quote(f"Failed to save LinkedIn details: {e}")
        redirect_url = f"{frontend_redirect_url}?linkedin_status=error&detail={error_detail}"
        return RedirectResponse(url=redirect_url)


    # 5. Redirect back to frontend on success
    redirect_url = f"{frontend_redirect_url}?linkedin_status=success"
    return RedirectResponse(url=redirect_url)


# --- Scheduling Endpoints ---

@router.post("/schedule", response_model=ScheduledLinkedInPostRead, status_code=status.HTTP_201_CREATED)
def schedule_linkedin_post(
    *,
    db: Session = Depends(get_session), # Corrected dependency
    post_in: ScheduledLinkedInPostCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Schedule a text post to be published on the user's LinkedIn profile.
    """
    # 1. Check if user has connected LinkedIn and token is valid (not expired)
    token_expires_at = current_user.linkedin_token_expires_at
    # Make the stored time timezone-aware (assume UTC) if it's naive
    if token_expires_at and token_expires_at.tzinfo is None:
        token_expires_at = token_expires_at.replace(tzinfo=timezone.utc)

    if not current_user.linkedin_access_token or \
       not token_expires_at or \
       token_expires_at <= datetime.now(timezone.utc): # Compare aware with aware
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LinkedIn account not connected or token expired. Please connect/reconnect via settings.",
        )

    # 2. Check if required scope is present (w_member_social)
    # Split scopes by comma OR space to handle both possibilities
    scopes_list = []
    if current_user.linkedin_scopes:
        scopes_list = [s.strip() for s in current_user.linkedin_scopes.replace(',', ' ').split()]

    logger.debug(f"Checking scopes for user {current_user.id}: {scopes_list}") # Debug log for scopes list
    if "w_member_social" not in scopes_list:
         logger.warning(f"User {current_user.id} missing 'w_member_social' scope. Granted: '{current_user.linkedin_scopes}'")
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Required LinkedIn permission 'w_member_social' not granted.",
        )

    # 3. Validate schedule time (e.g., must be in the future)
    # Ensure post_in.scheduled_at is timezone-aware (it should be if coming from ISO string)
    # If it might be naive, it needs to be localized or assumed UTC.
    # Assuming post_in.scheduled_at is already UTC after Pydantic validation from ISO string.
    # Add check to ensure it's aware before comparing
    scheduled_at_aware = post_in.scheduled_at
    if scheduled_at_aware.tzinfo is None:
         # This case might indicate an issue with Pydantic parsing or input format
         # For now, assume UTC if naive, but log a warning
         logger.warning(f"Received naive datetime for scheduled_at: {post_in.scheduled_at}. Assuming UTC.")
         scheduled_at_aware = scheduled_at_aware.replace(tzinfo=timezone.utc)

    if scheduled_at_aware < (datetime.now(timezone.utc) - timedelta(seconds=10)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scheduled time must be in the future.",
        )

    # 4. Create the scheduled post record
    # Ensure the user_id from the input matches the current user
    if post_in.user_id != current_user.id:
         raise HTTPException(
             status_code=status.HTTP_403_FORBIDDEN,
             detail="Cannot schedule post for another user.",
         )

    # Pass the potentially timezone-corrected scheduled_at to CRUD
    post_in.scheduled_at = scheduled_at_aware
    scheduled_post = crud.scheduled_post.create_scheduled_post(session=db, obj_in=post_in)
    return scheduled_post


@router.get("/scheduled", response_model=List[ScheduledLinkedInPostRead])
def list_scheduled_posts(
    db: Session = Depends(get_session), # Corrected dependency
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
) -> Any:
    """
    Retrieve scheduled LinkedIn posts for the current user.
    """
    posts = crud.scheduled_post.get_scheduled_posts_by_user(
        session=db, user_id=current_user.id, skip=skip, limit=limit
    )
    return posts


@router.delete("/schedule/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scheduled_linkedin_post(
    post_id: int,
    db: Session = Depends(get_session), # Corrected dependency
    current_user: User = Depends(deps.get_current_active_user),
) -> Response:
    """
    Delete a pending scheduled LinkedIn post.
    """
    deleted_post = crud.scheduled_post.delete_scheduled_post(
        session=db, post_id=post_id, user_id=current_user.id
    )
    if not deleted_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduled post not found, does not belong to user, or is not pending.",
        )
    # Return No Content on successful deletion
    return Response(status_code=status.HTTP_204_NO_CONTENT)

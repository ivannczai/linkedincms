"""
API endpoints for LinkedIn integration.
"""
import logging
from typing import List, Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
import requests
from sqlmodel import Session

from app.core.config import settings
from app.core.database import get_session
from app.core import oauth_state_manager # Import the manager
from app.api import deps # For user dependencies
from app.models.user import User # Import User model
from app import crud # Import crud module
from app.models.scheduled_post import ( # Import scheduled post models
    ScheduledLinkedInPost,
    ScheduledLinkedInPostCreate,
    ScheduledLinkedInPostRead,
    ScheduledLinkedInPostUpdate # Add update if needed later
)
from app.core.security import decrypt_data # Import decrypt_data

router = APIRouter()
logger = logging.getLogger(__name__)

# --- Helper Function for Redirects ---
def _redirect_to_frontend(params: dict):
    """Constructs a redirect response to the frontend settings page."""
    frontend_url = f"{settings.FRONTEND_URL_BASE}/dashboard/settings"
    query_string = urlencode(params)
    return RedirectResponse(f"{frontend_url}?{query_string}")


# --- LinkedIn OAuth Endpoints ---

@router.get("/connect", summary="Initiate LinkedIn Connection")
async def initiate_linkedin_connection(
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Generates the LinkedIn authorization URL and redirects the user.
    Stores a temporary state value associated with the user.
    """
    if not settings.LINKEDIN_CLIENT_ID or not settings.LINKEDIN_CLIENT_SECRET or not settings.LINKEDIN_REDIRECT_URI:
        logger.error("LinkedIn OAuth settings are not configured.")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="LinkedIn integration is not configured.")

    state = oauth_state_manager.generate_state()
    oauth_state_manager.store_state(state, current_user.id) # Store user ID with state

    # Define required scopes
    scopes = ["openid", "profile", "email", "w_member_social"] # Added w_member_social

    auth_url_params = {
        "response_type": "code",
        "client_id": settings.LINKEDIN_CLIENT_ID,
        "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
        "state": state,
        "scope": " ".join(scopes),
    }
    authorization_url = f"https://www.linkedin.com/oauth/v2/authorization?{urlencode(auth_url_params)}"

    # Instead of redirecting, return the URL for the frontend to handle
    return {"authorization_url": authorization_url}


@router.get("/connect/callback", summary="Handle LinkedIn OAuth Callback")
async def linkedin_connection_callback(
    request: Request, # Add Request to access session
    code: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    session: Session = Depends(get_session), # Add DB session dependency
):
    """
    Handles the callback from LinkedIn after user authorization.
    Exchanges the authorization code for an access token and stores it.
    """
    if error:
        logger.error(f"LinkedIn OAuth error: {error} - {error_description}")
        return _redirect_to_frontend({"linkedin_status": "error", "detail": error_description or error})

    if not code or not state:
        logger.error("LinkedIn callback missing code or state.")
        return _redirect_to_frontend({"linkedin_status": "error", "detail": "Missing authorization code or state"})

    # Verify state and get associated user ID
    user_id = oauth_state_manager.verify_and_consume_state(state)
    if not user_id:
        logger.warning("Invalid or expired state parameter received from LinkedIn callback.")
        return _redirect_to_frontend({"linkedin_status": "error", "detail": "Invalid or expired state"})

    # Exchange code for access token
    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    token_payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
        "client_id": settings.LINKEDIN_CLIENT_ID,
        "client_secret": settings.LINKEDIN_CLIENT_SECRET,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        response = requests.post(token_url, data=token_payload, headers=headers, timeout=15)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        token_data = response.json()
        access_token = token_data.get("access_token")
        expires_in = token_data.get("expires_in") # Typically 3600 seconds (1 hour) or 5184000 (60 days)
        scopes_string = token_data.get("scope", "") # e.g., "openid profile email w_member_social"
        logger.info(f"Received scopes from LinkedIn token exchange: {scopes_string}")

        if not access_token:
            raise ValueError("Access token not found in LinkedIn response.")

    except requests.exceptions.RequestException as e:
        error_detail = str(e)
        logger.error(f"LinkedIn token exchange failed: {error_detail}")
        return _redirect_to_frontend({"linkedin_status": "error", "detail": f"Token exchange failed: {error_detail}"})
    except ValueError as e:
        logger.error(f"Error processing LinkedIn token response: {e}")
        return _redirect_to_frontend({"linkedin_status": "error", "detail": f"Token processing error: {e}"})

    # Fetch user profile information (specifically the LinkedIn ID using the 'sub' field from OpenID Connect)
    userinfo_url = "https://api.linkedin.com/v2/userinfo"
    auth_header = {"Authorization": f"Bearer {access_token}"}

    try:
        userinfo_response = requests.get(userinfo_url, headers=auth_header, timeout=10)
        userinfo_response.raise_for_status()
        userinfo_data = userinfo_response.json()
        linkedin_id = userinfo_data.get("sub") # 'sub' is the standard OpenID field for user ID

        if not linkedin_id:
            raise ValueError("LinkedIn ID ('sub') not found in userinfo response.")

    except requests.exceptions.RequestException as e:
        error_detail = str(e)
        logger.error(f"Failed to fetch LinkedIn userinfo: {error_detail}")
        return _redirect_to_frontend({"linkedin_status": "error", "detail": f"Failed to fetch LinkedIn userinfo: {error_detail}"})
    except ValueError as e:
        logger.error(f"Error processing LinkedIn userinfo response: {e}")
        return _redirect_to_frontend({"linkedin_status": "error", "detail": f"Userinfo processing error: {e}"})


    # Calculate expiry time
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in) if expires_in else None

    # Store LinkedIn details for the user
    try:
        user = crud.user.get(session=session, user_id=user_id)
        if not user:
            # This should ideally not happen if state verification worked
            logger.error(f"User with ID {user_id} not found after state verification.")
            return _redirect_to_frontend({"linkedin_status": "error", "detail": "User not found"})

        linkedin_details = {
            "linkedin_id": linkedin_id,
            "linkedin_access_token": access_token, # Will be encrypted by CRUD function
            "linkedin_token_expires_at": expires_at,
            "linkedin_scopes": scopes_string,
        }
        crud.user.update_linkedin_details(session=session, db_obj=user, linkedin_data=linkedin_details)
        logger.info(f"Successfully stored LinkedIn details for user ID {user_id}")

    except Exception as e:
        # Catch potential database errors during update
        error_detail = str(e)
        logger.error(f"Failed to save LinkedIn details for user ID {user_id}: {error_detail}", exc_info=True)
        # Include specific error in redirect detail
        return _redirect_to_frontend({"linkedin_status": "error", "detail": f"Failed to save LinkedIn details: {error_detail}"})

    # Redirect back to frontend settings page on success
    return _redirect_to_frontend({"linkedin_status": "success"})


# --- LinkedIn Post Scheduling Endpoints ---

@router.post("/schedule", response_model=ScheduledLinkedInPostRead, status_code=status.HTTP_201_CREATED)
async def schedule_linkedin_post(
    *,
    session: Session = Depends(get_session),
    post_in: ScheduledLinkedInPostCreate,
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Schedule a post to be published on LinkedIn.
    """
    # 1. Verify user has valid, non-expired LinkedIn token with correct scope
    decrypted_token = None
    if current_user.linkedin_access_token:
        decrypted_token = decrypt_data(current_user.linkedin_access_token)

    token_expires_at = current_user.linkedin_token_expires_at
    # Ensure expiry is timezone-aware for comparison
    if token_expires_at and token_expires_at.tzinfo is None:
         token_expires_at = token_expires_at.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)

    if not decrypted_token or not token_expires_at or token_expires_at <= now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LinkedIn connection is invalid or token expired. Please reconnect on the settings page.",
        )

    # Check for required scope
    scopes_list = []
    if current_user.linkedin_scopes:
         scopes_list = [s.strip() for s in current_user.linkedin_scopes.replace(',', ' ').split()]

    if "w_member_social" not in scopes_list:
         raise HTTPException(
             status_code=status.HTTP_403_FORBIDDEN,
             detail="Required LinkedIn permission 'w_member_social' not granted. Please reconnect on the settings page.",
         )

    # 2. Validate schedule time is in the future
    scheduled_at_utc = post_in.scheduled_at
    if scheduled_at_utc.tzinfo is None:
        # Assume UTC if no timezone provided (should come as ISO string from frontend)
        scheduled_at_utc = scheduled_at_utc.replace(tzinfo=timezone.utc)

    if scheduled_at_utc <= now:
         raise HTTPException(
             status_code=status.HTTP_400_BAD_REQUEST,
             detail="Scheduled time must be in the future.",
         )

    # 3. Create the scheduled post record (ensure user_id matches current user)
    # Add user_id from the authenticated user to the input object
    post_create_data = post_in.model_dump()
    post_create_data["user_id"] = current_user.id
    # Re-create the Pydantic model to ensure validation
    validated_post_in = ScheduledLinkedInPostCreate(**post_create_data)

    scheduled_post = crud.scheduled_post.create_scheduled_post(session=session, obj_in=validated_post_in)
    logger.info(f"User ID {current_user.id} scheduled LinkedIn post ID {scheduled_post.id} for {scheduled_post.scheduled_at}")
    return scheduled_post


@router.get("/scheduled", response_model=List[ScheduledLinkedInPostRead])
async def list_scheduled_posts(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieve scheduled LinkedIn posts for the current user.
    """
    posts = crud.scheduled_post.get_scheduled_posts_by_user(
        session=session, user_id=current_user.id, skip=skip, limit=limit
    )
    return posts


@router.delete("/schedule/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scheduled_post(
    *,
    session: Session = Depends(get_session),
    post_id: int,
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Delete a PENDING scheduled LinkedIn post.
    """
    deleted_post = crud.scheduled_post.delete_pending_post(
        session=session, post_id=post_id, user_id=current_user.id
    )
    if not deleted_post:
        # Raise 404 if post not found OR if it wasn't pending/didn't belong to user
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pending scheduled post not found or you do not have permission to delete it.",
        )
    logger.info(f"User ID {current_user.id} deleted pending LinkedIn post ID {post_id}")
    return None # Return None for 204 response

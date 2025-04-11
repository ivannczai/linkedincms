"""
Main FastAPI application module for Winning Sales Content Hub.
"""
import logging
import time # Import time for sleep
from contextlib import asynccontextmanager # Import asynccontextmanager for lifespan
from datetime import datetime, timezone, timedelta # Import timedelta

from fastapi import FastAPI, Depends, Request # Import Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware # Import BaseHTTPMiddleware
from starlette.responses import Response # Import Response
from sqlmodel import Session, select
from apscheduler.schedulers.background import BackgroundScheduler # Import scheduler
import requests # Import requests for publishing job

from app.api.api import api_router
from app.core.config import settings # Import settings
from app.core.database import create_db_and_tables, get_session, engine # Import engine for session creation in job
from app.models.user import User, UserRole # Import User model and Role
from app.models.scheduled_post import PostStatus # Import PostStatus
from app.core.security import get_password_hash, decrypt_data # Import decrypt_data
from app import crud # Import crud

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Scheduler Setup ---
scheduler = BackgroundScheduler(timezone="UTC") # Use UTC for consistency
MAX_RETRIES = 3 # Define max number of retries
RETRY_DELAY_MINUTES = 5 # Base delay in minutes for first retry

def is_retryable_error(e: requests.exceptions.RequestException) -> bool:
    """Check if a requests exception indicates a potentially temporary issue."""
    if isinstance(e, (requests.exceptions.Timeout, requests.exceptions.ConnectionError)):
        return True
    if e.response is not None:
        # Retry on server errors (5xx) and rate limiting (429)
        return e.response.status_code >= 500 or e.response.status_code == 429
    return False

def publish_scheduled_linkedin_posts():
    """
    Job function executed by the scheduler to publish due posts.
    Includes retry logic for transient errors.
    """
    logger.info("Scheduler: Checking for LinkedIn posts to publish...")
    with Session(engine) as session:
        try:
            now = datetime.now(timezone.utc)
            # Fetch posts scheduled for now or earlier, AND whose retry count is acceptable
            pending_posts = crud.scheduled_post.get_pending_posts_to_publish(session=session, now=now)
            logger.info(f"Scheduler: Found {len(pending_posts)} posts due for publishing.")

            for post in pending_posts:
                # Skip if already processed in this run (e.g., if retried immediately)
                # This check might be redundant if get_pending_posts filters correctly, but adds safety
                if post.status != PostStatus.PENDING or post.scheduled_at > now:
                     continue

                logger.info(f"Scheduler: Attempting to publish post ID {post.id} (Retry {post.retry_count}) for user ID {post.user_id}")
                user = crud.user.get(session=session, user_id=post.user_id)
                error_message_prefix = f"Failed Post ID {post.id}: "

                if not user:
                    logger.error(f"Scheduler: User ID {post.user_id} not found for post ID {post.id}. Failing permanently.")
                    crud.scheduled_post.update_post_status(
                        session=session, db_obj=post, status=PostStatus.FAILED, error_message=error_message_prefix + "User not found"
                    )
                    continue

                # Decrypt the stored access token
                decrypted_access_token = None
                if user.linkedin_access_token:
                    decrypted_access_token = decrypt_data(user.linkedin_access_token)

                # Check token validity
                token_expires_at = user.linkedin_token_expires_at
                if token_expires_at and token_expires_at.tzinfo is None:
                    token_expires_at = token_expires_at.replace(tzinfo=timezone.utc)

                if not decrypted_access_token or not token_expires_at or token_expires_at <= now:
                    logger.warning(f"Scheduler: LinkedIn token invalid, expired, or failed decryption for user ID {user.id}, post ID {post.id}. Failing permanently.")
                    crud.scheduled_post.update_post_status(
                        session=session, db_obj=post, status=PostStatus.FAILED, error_message=error_message_prefix + "Token expired or invalid/decryption failed"
                    )
                    continue

                # Check scope
                scopes_list = []
                if user.linkedin_scopes:
                    scopes_list = [s.strip() for s in user.linkedin_scopes.replace(',', ' ').split()]

                if "w_member_social" not in scopes_list:
                    logger.warning(f"Scheduler: Missing 'w_member_social' scope for user ID {user.id}, post ID {post.id}. Failing permanently. Granted: '{user.linkedin_scopes}'")
                    crud.scheduled_post.update_post_status(
                        session=session, db_obj=post, status=PostStatus.FAILED, error_message=error_message_prefix + "Missing required scope 'w_member_social'"
                    )
                    continue

                # --- Call LinkedIn API to publish ---
                post_payload = {
                    "author": f"urn:li:person:{user.linkedin_id}",
                    "lifecycleState": "PUBLISHED",
                    "specificContent": {
                        "com.linkedin.ugc.ShareContent": {
                            "shareCommentary": {"text": post.content_text},
                            "shareMediaCategory": "NONE"
                        }
                    },
                    "visibility": {
                        "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                    }
                }
                headers = {
                    "Authorization": f"Bearer {decrypted_access_token}",
                    "X-Restli-Protocol-Version": "2.0.0",
                    "Content-Type": "application/json"
                }
                linkedin_post_url = "https://api.linkedin.com/v2/ugcPosts"

                try:
                    response = requests.post(linkedin_post_url, headers=headers, json=post_payload, timeout=30)
                    response.raise_for_status()
                    linkedin_post_id = response.headers.get("X-RestLi-Id") or response.headers.get("x-restli-id")
                    logger.info(f"Scheduler: Successfully published post ID {post.id} to LinkedIn. LinkedIn Post ID: {linkedin_post_id}")
                    crud.scheduled_post.update_post_status(
                        session=session, db_obj=post, status=PostStatus.PUBLISHED, linkedin_post_id=linkedin_post_id
                    )

                except requests.exceptions.RequestException as e:
                    # Check if error is retryable and retry limit not reached
                    if post.retry_count < MAX_RETRIES and is_retryable_error(e):
                        retry_delay_seconds = (RETRY_DELAY_MINUTES * 60) * (2 ** post.retry_count) # Exponential backoff (5m, 20m, 80m)
                        new_schedule_time = now + timedelta(seconds=retry_delay_seconds)
                        retry_msg = f"API Error (Retry {post.retry_count + 1}/{MAX_RETRIES} scheduled for {new_schedule_time.isoformat()}): {e}"
                        logger.warning(f"Scheduler: Post ID {post.id} failed with retryable error. {retry_msg}")
                        crud.scheduled_post.update_for_retry(
                            session=session,
                            db_obj=post,
                            new_scheduled_at=new_schedule_time,
                            retry_error_message=retry_msg[:255] # Truncate if needed
                        )
                    else:
                        # Not retryable or max retries reached - fail permanently
                        error_detail = f"API Error: {e.response.status_code} - {e.response.text}" if e.response else f"Request Error: {e}"
                        logger.error(f"Scheduler: Failed to publish post ID {post.id} after {post.retry_count} retries or due to non-retryable error. {error_detail}")
                        crud.scheduled_post.update_post_status(
                            session=session, db_obj=post, status=PostStatus.FAILED, error_message=(error_message_prefix + error_detail)[:255]
                        )
                except Exception as e:
                    # Catch any other unexpected errors during publishing
                    logger.error(f"Scheduler: Unexpected error publishing post ID {post.id}: {e}", exc_info=True)
                    crud.scheduled_post.update_post_status(
                        session=session, db_obj=post, status=PostStatus.FAILED, error_message=(error_message_prefix + f"Unexpected error: {str(e)[:200]}")
                    )
            logger.info("Scheduler: Finished checking posts.")
        except Exception as e:
            # Catch broad exceptions during the whole check cycle
            logger.error(f"Scheduler: Error during post publishing cycle: {e}", exc_info=True)


# --- FastAPI Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Running application startup tasks...")
    # Superuser creation is now handled by entrypoint.sh for Docker deployments
    # For local dev, it needs to be run manually via the script.

    # Start the scheduler
    try:
        scheduler.add_job(publish_scheduled_linkedin_posts, 'interval', minutes=1, id='publish_linkedin_job', replace_existing=True)
        scheduler.start()
        logger.info("Scheduler started.")
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")

    logger.info("Application startup tasks complete.")
    yield # Application runs here
    # Shutdown
    logger.info("Running application shutdown tasks...")
    try:
        scheduler.shutdown()
        logger.info("Scheduler shut down gracefully.")
    except Exception as e:
        logger.error(f"Error shutting down scheduler: {e}")
    logger.info("Application shutdown complete.")


app = FastAPI(
    title="Winning Sales Content Hub API",
    description="API for managing sales content collaboration between Winning Sales and clients",
    version="0.1.0",
    lifespan=lifespan # Use the lifespan context manager
)

# --- Middleware ---

# Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        # Add other headers as needed (e.g., CSP, Referrer-Policy)
        # response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# CORS Middleware (should generally be one of the last middlewares)
# Split the comma-separated string from settings into a list
cors_origins = [origin.strip() for origin in settings.BACKEND_CORS_ORIGINS.split(',') if origin]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins, # Use the processed list
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


# Removed create_first_superuser function as it's now handled by the script


@app.get("/")
async def root():
    """
    Root endpoint that returns a welcome message.

    Returns:
        dict: A simple welcome message
    """
    return {"message": "Welcome to Winning Sales Content Hub API"}


@app.get("/healthcheck")
async def healthcheck(session: Session = Depends(get_session)):
    """
    Healthcheck endpoint that verifies database connection.

    Args:
        session: Database session dependency

    Returns:
        dict: Status message
    """
    # Simple query to verify database connection
    try:
        # Use a more specific query that doesn't rely on exceptions for flow control
        result = session.execute(select(1))
        if result.scalar_one() == 1:
             return {"status": "healthy", "database": "connected"}
        else:
             # This case should ideally not happen with 'SELECT 1'
             return {"status": "unhealthy", "database": "query failed"}
    except Exception as e:
        logger.error(f"Healthcheck database connection error: {e}")
        return {"status": "unhealthy", "database": "connection error"}


if __name__ == "__main__":
    import uvicorn

    # Use settings for host and port if defined, otherwise default
    host = getattr(settings, "HOST", "0.0.0.0")
    port = getattr(settings, "PORT", 8000)
    reload = getattr(settings, "RELOAD", True) # Assuming RELOAD setting might exist

    # Note: Uvicorn's reload doesn't work well with APScheduler background threads.
    # For development with scheduler, consider running without reload or using
    # a different approach like Celery. For now, keep reload=False if scheduler is active.
    uvicorn.run("app.main:app", host=host, port=port, reload=False) # Set reload=False when using scheduler

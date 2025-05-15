"""
CRUD operations for ScheduledLinkedInPost model.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import status
from sqlmodel import Session, select

from app.models.scheduled_post import (
    ScheduledLinkedInPost,
    ScheduledLinkedInPostCreate,
    ScheduledLinkedInPostUpdate, # Keep for potential future use
    PostStatus
)

class PostDeletionError(Exception):
    """Custom exception for post deletion errors."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)

def create_scheduled_post(
    session: Session, *, obj_in: ScheduledLinkedInPostCreate
) -> ScheduledLinkedInPost:
    """
    Create a new scheduled LinkedIn post record.

    Args:
        session: Database session.
        obj_in: Data for the new scheduled post.

    Returns:
        The created ScheduledLinkedInPost object.
    """
    # Create the database object, status defaults to PENDING, retry_count defaults to 0
    db_obj = ScheduledLinkedInPost.model_validate(obj_in)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def get_scheduled_post(session: Session, post_id: int) -> Optional[ScheduledLinkedInPost]:
    """
    Get a scheduled post by its ID.

    Args:
        session: Database session.
        post_id: The ID of the post to retrieve.

    Returns:
        The ScheduledLinkedInPost object if found, otherwise None.
    """
    return session.get(ScheduledLinkedInPost, post_id)


def get_scheduled_posts_by_user(
    session: Session, *, user_id: int, skip: int = 0, limit: int = 100
) -> List[ScheduledLinkedInPost]:
    """
    Get scheduled posts for a specific user, ordered by scheduled time.

    Args:
        session: Database session.
        user_id: The ID of the user whose posts to retrieve.
        skip: Number of posts to skip (for pagination).
        limit: Maximum number of posts to return (for pagination).

    Returns:
        A list of ScheduledLinkedInPost objects.
    """
    statement = (
        select(ScheduledLinkedInPost)
        .where(ScheduledLinkedInPost.user_id == user_id)
        .order_by(ScheduledLinkedInPost.scheduled_at.desc()) # Show newest first, adjust if needed
        .offset(skip)
        .limit(limit)
    )
    return session.exec(statement).all()


def get_pending_posts_to_publish(session: Session, *, now: datetime) -> List[ScheduledLinkedInPost]:
    """
    Get all pending scheduled posts that are due to be published.

    Args:
        session: Database session.
        now: The current time (timezone-aware recommended).

    Returns:
        A list of pending ScheduledLinkedInPost objects ready for publishing.
    """
    statement = (
        select(ScheduledLinkedInPost)
        .where(ScheduledLinkedInPost.status == PostStatus.PENDING)
        .where(ScheduledLinkedInPost.scheduled_at <= now)
        .order_by(ScheduledLinkedInPost.scheduled_at) # Process oldest first
    )
    return session.exec(statement).all()


def update_post_status(
    session: Session,
    *,
    db_obj: ScheduledLinkedInPost,
    status: PostStatus,
    linkedin_post_id: Optional[str] = None,
    error_message: Optional[str] = None
) -> ScheduledLinkedInPost:
    """
    Update the status of a scheduled post (e.g., after publishing or permanent failure).

    Args:
        session: Database session.
        db_obj: The ScheduledLinkedInPost object to update.
        status: The new status (PUBLISHED or FAILED).
        linkedin_post_id: The ID returned by LinkedIn API upon successful publishing.
        error_message: The error message if publishing failed permanently.

    Returns:
        The updated ScheduledLinkedInPost object.
    """
    db_obj.status = status
    if status == PostStatus.PUBLISHED:
        db_obj.linkedin_post_id = linkedin_post_id
        db_obj.error_message = None # Clear any previous error
        db_obj.retry_count = 0 # Reset retry count on success
    elif status == PostStatus.FAILED:
        db_obj.error_message = error_message
        db_obj.linkedin_post_id = None # Clear any previous post ID
        # retry_count is not reset here, it reflects the count when it failed

    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_for_retry(
    session: Session,
    *,
    db_obj: ScheduledLinkedInPost,
    new_scheduled_at: datetime,
    retry_error_message: str
) -> ScheduledLinkedInPost:
    """
    Update a scheduled post for a retry attempt. Increments retry count,
    updates scheduled time, and sets a temporary error message.

    Args:
        session: Database session.
        db_obj: The ScheduledLinkedInPost object to update.
        new_scheduled_at: The new time to schedule the retry for.
        retry_error_message: Message indicating a retry is scheduled.

    Returns:
        The updated ScheduledLinkedInPost object.
    """
    db_obj.retry_count += 1
    db_obj.scheduled_at = new_scheduled_at
    db_obj.error_message = retry_error_message
    # Status remains PENDING

    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def delete_scheduled_post(session: Session, *, post_id: int, user_id: int) -> Optional[ScheduledLinkedInPost]:
    """
    Delete a scheduled post by ID, ensuring it belongs to the correct user and is pending.

    Args:
        session: Database session.
        post_id: The ID of the post to delete.
        user_id: The ID of the user requesting the deletion.

    Returns:
        The deleted ScheduledLinkedInPost object if found and deleted, otherwise None.

    Raises:
        PostDeletionError: If the post is not in PENDING status.
    """
    db_obj = session.exec(
        select(ScheduledLinkedInPost)
        .where(ScheduledLinkedInPost.id == post_id)
        .where(ScheduledLinkedInPost.user_id == user_id)
    ).first()

    if not db_obj:
        return None # Not found or doesn't belong to user

    # Optional: Only allow deletion if status is PENDING
    if db_obj.status != PostStatus.PENDING:
        raise PostDeletionError("Can only delete posts that are in PENDING status.")

    session.delete(db_obj)
    session.commit()
    # The object is expired after deletion, so we return it as it was before deletion
    # Or just return True/False for success/failure
    return db_obj

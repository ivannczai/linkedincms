"""
ContentPiece CRUD operations module.

This module contains CRUD operations for the ContentPiece model.
"""
from typing import List, Optional, Union, Dict, Any
from datetime import datetime
import bleach # Import bleach for sanitization

from sqlmodel import Session, select, SQLModel # Import SQLModel
from sqlalchemy import desc, asc # Import asc and desc for sorting
from fastapi import HTTPException, status
from pydantic import validator, Field

from app.models.content import ContentPiece, ContentPieceCreate, ContentPieceUpdate, ContentStatus
from app.models.user import User, UserRole # Import User for permission checks

# --- Bleach Configuration ---
# Define allowed HTML tags and attributes suitable for basic rich text
ALLOWED_TAGS = [
    'p', 'br', 'b', 'strong', 'i', 'em', 'ul', 'ol', 'li', 'a'
]
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target'], # Allow standard link attributes
}
# --------------------------


def sanitize_html(html_content: Optional[str]) -> Optional[str]:
    """Sanitizes HTML content using bleach."""
    if html_content is None:
        return None
    return bleach.clean(
        html_content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True # Remove disallowed tags completely
    )


def get(session: Session, content_id: int) -> Optional[ContentPiece]:
    """
    Get a content piece by ID.
    """
    return session.get(ContentPiece, content_id)


def get_multi(
    session: Session,
    *,
    client_id: Optional[int] = None,
    status: Optional[ContentStatus] = None,
    sort_by: Optional[str] = None, # Add sort_by parameter
    sort_order: str = "desc", # Add sort_order parameter (default desc)
    skip: int = 0,
    limit: int = 100,
) -> List[ContentPiece]:
    """
    Get multiple content pieces, optionally filtered and sorted.
    """
    query = select(ContentPiece)

    if client_id is not None:
        query = query.where(ContentPiece.client_id == client_id)

    if status is not None:
        query = query.where(ContentPiece.status == status)

    # Apply sorting
    if sort_by:
        sort_column = getattr(ContentPiece, sort_by, None)
        if sort_column:
            if sort_order.lower() == "asc":
                query = query.order_by(asc(sort_column))
            else:
                query = query.order_by(desc(sort_column))
        else:
            # Handle invalid sort_by field if necessary, e.g., log a warning or raise error
            print(f"Warning: Invalid sort_by field provided: {sort_by}")
            # Default sort if invalid field provided (optional)
            query = query.order_by(desc(ContentPiece.created_at)) 
    else:
         # Default sort if no sort_by provided
         query = query.order_by(desc(ContentPiece.created_at))


    return session.exec(query.offset(skip).limit(limit)).all()


def create(session: Session, *, obj_in: ContentPieceCreate) -> ContentPiece:
    """
    Create a new content piece, sanitizing HTML content.
    """
    # Sanitize HTML content before creating the object
    sanitized_body = sanitize_html(obj_in.content_body)

    # Create a dictionary from the input object to modify it
    obj_in_data = obj_in.dict()
    obj_in_data['content_body'] = sanitized_body # Use sanitized content

    # Create the DB object from the modified dictionary
    db_obj = ContentPiece(**obj_in_data)

    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update(
    session: Session,
    *,
    db_obj: ContentPiece,
    obj_in: Union[ContentPieceUpdate, Dict[str, Any]]
) -> ContentPiece:
    """
    Update a content piece, sanitizing HTML content if provided.
    """
    if isinstance(obj_in, dict):
        update_data = obj_in
    else:
        # Use exclude_unset=True to only update provided fields
        update_data = obj_in.dict(exclude_unset=True)

    # Sanitize content_body if it's being updated
    if 'content_body' in update_data:
        update_data['content_body'] = sanitize_html(update_data['content_body'])

    for field, value in update_data.items():
        setattr(db_obj, field, value)

    # Ensure updated_at is set
    db_obj.updated_at = datetime.utcnow()

    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def delete(session: Session, *, content_id: int) -> Optional[ContentPiece]:
    """
    Delete a content piece.
    """
    content = session.get(ContentPiece, content_id)
    if content:
        session.delete(content)
        session.commit()
    return content


def update_status(
    session: Session,
    *,
    content_id: int,
    new_status: ContentStatus,
    review_comment: Optional[str] = None
) -> ContentPiece:
    """
    Update the status of a content piece.
    """
    db_obj = get(session, content_id)
    if not db_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content piece not found")

    db_obj.status = new_status
    if new_status == ContentStatus.REVISION_REQUESTED:
        # Sanitize review comment as well? Decide based on requirements.
        # For now, assuming plain text is acceptable for comments.
        db_obj.review_comment = review_comment
    elif db_obj.review_comment is not None and new_status != ContentStatus.REVISION_REQUESTED:
         # Clear comment if status changes away from revision requested
         db_obj.review_comment = None

    # Set published_at timestamp if status is PUBLISHED
    if new_status == ContentStatus.PUBLISHED and db_obj.published_at is None:
        db_obj.published_at = datetime.utcnow()

    db_obj.updated_at = datetime.utcnow()
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj

def mark_as_posted(session: Session, *, content_id: int) -> ContentPiece:
    """
    Mark a content piece as posted by setting the published_at timestamp.
    Typically done after the content is approved and manually posted by the client.
    """
    db_obj = get(session, content_id)
    if not db_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content piece not found")

    # Allow marking as posted only if approved, scheduled or already published
    if db_obj.status not in [ContentStatus.APPROVED, ContentStatus.SCHEDULED, ContentStatus.PUBLISHED]:
         raise HTTPException(
             status_code=status.HTTP_400_BAD_REQUEST,
             detail="Content must be approved or scheduled to be marked as posted."
         )

    if db_obj.published_at is None:
        db_obj.published_at = datetime.utcnow()
        db_obj.status = ContentStatus.PUBLISHED # Also update status
        db_obj.updated_at = datetime.utcnow()
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)

    # If already published, just return the object without changes
    return db_obj

# --- New Rating Function ---
class ContentRatingInput(SQLModel):
    """Schema for rating input."""
    rating: float = Field(..., ge=0, le=5) # Rating between 0 and 5

    @validator('rating')
    def rating_must_be_half_step(cls, v):
        if (v * 2) % 1 != 0:
            raise ValueError('Rating must be in 0.5 increments')
        return v

def rate_content(
    session: Session,
    *,
    content_id: int,
    rating_in: ContentRatingInput,
    client_user: User # Pass the authenticated client user for permission check
) -> ContentPiece:
    """
    Allows a client to rate an approved content piece.
    """
    db_obj = get(session, content_id)
    if not db_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content piece not found")

    # Permission Check: Ensure the user is the client associated with this content
    # Check if client_profile exists before accessing id
    if not client_user.client_profile or db_obj.client_id != client_user.client_profile.id:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to rate this content")

    # Status Check: Allow rating only if content is approved or published
    if db_obj.status not in [ContentStatus.APPROVED, ContentStatus.PUBLISHED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content must be approved or published before rating."
        )

    db_obj.client_rating = rating_in.rating
    db_obj.updated_at = datetime.utcnow()
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj

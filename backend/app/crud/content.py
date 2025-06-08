"""
ContentPiece CRUD operations module.

This module contains CRUD operations for the ContentPiece model.
"""
from typing import List, Optional, Union, Dict, Any
from datetime import datetime
import bleach # Import bleach for sanitization
import os
import logging
from fastapi import UploadFile
import json

from sqlmodel import Session, select, SQLModel # Import SQLModel
from sqlalchemy import desc, asc # Import asc and desc for sorting
from fastapi import HTTPException, status
from pydantic import validator, Field

from app.models.content import ContentPiece, ContentPieceCreate, ContentPieceUpdate, ContentStatus
from app.models.user import User, UserRole # Import User for permission checks
from app.crud.base import CRUDBase
from app.utils.file_utils import save_upload_file
from app.services.linkedin import upload_to_linkedin

# --- Bleach Configuration ---
# Define allowed HTML tags and attributes suitable for basic rich text
ALLOWED_TAGS = [
    'p', 'br', 'b', 'strong', 'i', 'em', 'ul', 'ol', 'li', 'a'
]
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target'], # Allow standard link attributes
}
# --------------------------

logger = logging.getLogger(__name__)

class CRUDContent(CRUDBase[ContentPiece, ContentPieceCreate, ContentPieceUpdate]):
    async def create(
        self,
        *,
        session: Session,
        obj_in: ContentPieceCreate,
        attachments: Optional[List[UploadFile]] = None
    ) -> ContentPiece:
        """Create new content piece with optional attachments."""
        db_obj = ContentPiece.from_orm(obj_in)
        
        # Save attachments if provided
        if attachments:
            attachment_paths = []
            for file in attachments:
                try:
                    # Generate unique filename
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{timestamp}_{file.filename}"
                    file_path = f"uploads/{filename}"
                    
                    # Save file
                    await save_upload_file(file, file_path)
                    attachment_paths.append(file_path)
                except Exception as e:
                    logger.error(f"Error saving attachment {file.filename}: {str(e)}")
                    continue
            
            if attachment_paths:
                db_obj.attachments = attachment_paths
            else:
                db_obj.attachments = None

        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: Session,
        *,
        db_obj: ContentPiece,
        obj_in: ContentPieceUpdate,
        user: Optional[User] = None,
        attachments: Optional[List[UploadFile]] = None,
        existing_attachments: Optional[List[str]] = None
    ) -> ContentPiece:
        """Update a content piece."""
        update_data = obj_in.dict(exclude_unset=True)
        
        # Обробка файлів
        if attachments or existing_attachments:
            attachment_paths = []
            
            # Додаємо існуючі файли
            if existing_attachments:
                attachment_paths.extend(existing_attachments)
                
            # Додаємо нові файли
            if attachments:
                for file in attachments:
                    try:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"{timestamp}_{file.filename}"
                        file_path = f"uploads/{filename}"
                        
                        # Зберігаємо файл
                        await save_upload_file(file, file_path)
                        attachment_paths.append(file_path)
                    except Exception as e:
                        logger.error(f"Error saving attachment {file.filename}: {str(e)}")
                        continue
            
            if attachment_paths:
                db_obj.attachments = attachment_paths
            else:
                db_obj.attachments = None
        
        # Перевірка статусу та завантаження в LinkedIn
        if "status" in update_data and update_data["status"] in [ContentStatus.SCHEDULED, ContentStatus.PUBLISHED]:
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User is required for LinkedIn upload"
                )
            
            if not db_obj.linkedin_media_assets and db_obj.attachments:
                try:
                    media_assets = []
                    
                    for attachment in db_obj.attachments:
                        try:
                            upload_info = await linkedinService.register_upload(
                                access_token=user.linkedin_access_token,
                                user_id=user.linkedin_id,
                                file_type="image/jpeg",  # TODO: визначити тип файлу
                                file_size=os.path.getsize(attachment)
                            )
                            
                            await linkedinService.upload_file(
                                upload_url=upload_info["uploadUrl"],
                                file_path=attachment
                            )
                            
                            media_assets.append(upload_info["asset"])
                        except Exception as e:
                            logger.error(f"Failed to upload {attachment} to LinkedIn: {str(e)}")
                            continue
                    
                    if media_assets:
                        db_obj.linkedin_media_assets = media_assets
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Failed to upload any files to LinkedIn"
                        )
                except Exception as e:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Failed to process LinkedIn uploads: {str(e)}"
                    )
        
        for field, value in update_data.items():
            if field != "attachments":  # Skip attachments, we already processed them
                setattr(db_obj, field, value)
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_by_client(
        self, session: Session, *, client_id: int, skip: int = 0, limit: int = 100
    ) -> List[ContentPiece]:
        """Get all content pieces for a client."""
        statement = select(ContentPiece).where(
            ContentPiece.client_id == client_id
        ).offset(skip).limit(limit)
        return session.exec(statement).all()

content = CRUDContent(ContentPiece)

# Export the update function
update = content.update

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
    review_comment: Optional[str] = None,
    scheduled_at: Optional[datetime] = None
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

    # Set scheduled_at if provided
    if scheduled_at is not None:
        db_obj.scheduled_at = scheduled_at

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

"""
Scheduled LinkedIn Post model module.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any

from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import TEXT, Column
from sqlalchemy.dialects.postgresql import JSONB

from app.models.base import BaseModel, TimestampMixin
# Import User model for relationship typing, avoid circular import if needed
# from app.models.user import User


class PostStatus(str, Enum):
    """
    Enum for the status of a scheduled post.
    """
    PENDING = "pending"
    PUBLISHED = "published"
    FAILED = "failed"
    DELETED = "deleted"


class ScheduledLinkedInPostBase(SQLModel):
    """
    Base model for ScheduledLinkedInPost with common fields.
    """
    user_id: int = Field(foreign_key="user.id", index=True)
    content_id: Optional[int] = Field(default=None, foreign_key="contentpiece.id", index=True) # Link to content if exists
    # Correctly specify TEXT type using sa_type
    content_text: str = Field(sa_type=TEXT)
    scheduled_at: datetime = Field(index=True)
    status: PostStatus = Field(default=PostStatus.PENDING, index=True)
    linkedin_post_id: Optional[str] = Field(default=None, index=True) # Store the ID returned by LinkedIn API
    error_message: Optional[str] = Field(default=None)
    retry_count: int = Field(default=0) # Added retry counter
    media_assets: Optional[List[Dict[str, Any]]] = Field(default=None, sa_column=Column(JSONB)) # Store LinkedIn media asset objects

    def __init__(self, **data):
        super().__init__(**data)
        # Convert scheduled_at to UTC if it has timezone info
        if self.scheduled_at and self.scheduled_at.tzinfo is not None:
            self.scheduled_at = self.scheduled_at.astimezone(timezone.utc)
        elif self.scheduled_at:
            self.scheduled_at = self.scheduled_at.replace(tzinfo=timezone.utc)


class ScheduledLinkedInPost(BaseModel, ScheduledLinkedInPostBase, TimestampMixin, table=True):
    """
    Database model for a scheduled LinkedIn post.
    """
    # Define relationship if needed (e.g., to access user details from post)
    # user: "User" = Relationship(back_populates="scheduled_posts") # Add scheduled_posts to User model if needed
    pass


class ScheduledLinkedInPostCreate(ScheduledLinkedInPostBase):
    """
    Schema for creating a scheduled post via API.
    Status, linkedin_post_id, error_message, retry_count are set by the system.
    """
    # Exclude fields set by the system during creation if necessary,
    # but Pydantic usually handles extra fields if the model validates.
    # For clarity, we could define specific fields here if needed.
    pass


class ScheduledLinkedInPostRead(ScheduledLinkedInPostBase, BaseModel, TimestampMixin):
    """
    Schema for reading scheduled post data via API.
    Includes all fields including generated ones like id, created_at etc.
    """
    pass


class ScheduledLinkedInPostUpdate(SQLModel):
    """
    Schema for updating a scheduled post (e.g., cancelling - might just use DELETE).
    Potentially could allow editing content/time if status is pending.
    """
    content_text: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    # Status update would likely be internal via scheduler or cancellation endpoint

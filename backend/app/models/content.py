"""
Content model module.

This module contains the ContentPiece model and related schemas.
"""
from typing import Optional, List, TYPE_CHECKING
from datetime import date, datetime
from enum import Enum, auto

from pydantic import validator
from sqlmodel import Field, SQLModel, Relationship, Column, Float # Add Column and Float
from sqlalchemy import DateTime # Import DateTime for timezone support

from app.models.base import BaseModel, TimestampMixin

if TYPE_CHECKING:
    from app.models.client import ClientProfile


class ContentStatus(str, Enum):
    """
    Enum for content piece status.
    """
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    REVISION_REQUESTED = "REVISION_REQUESTED"
    APPROVED = "APPROVED"
    PUBLISHED = "PUBLISHED"


class ContentPieceBase(SQLModel):
    """
    Base model for ContentPiece with common fields.
    """
    title: str = Field(index=True)
    idea: str
    angle: str
    content_body: str
    status: ContentStatus = Field(default=ContentStatus.DRAFT)
    due_date: Optional[date] = None
    is_active: bool = Field(default=True)


class ContentPiece(BaseModel, ContentPieceBase, TimestampMixin, table=True):
    """
    ContentPiece model for database.
    
    This model represents a content piece in the system, which is linked to a client profile.
    """
    # Foreign key to ClientProfile
    client_id: int = Field(foreign_key="clientprofile.id")
    
    # Optional review comment
    review_comment: Optional[str] = None
    
    # Optional published timestamp
    published_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    
    # Optional client rating
    client_rating: Optional[float] = Field(default=None, sa_type=Float) # Add rating field
    
    # Relationships
    client_profile: "ClientProfile" = Relationship(back_populates="content_pieces")


class ContentPieceCreate(ContentPieceBase):
    """
    Schema for creating a new content piece.
    """
    client_id: int
    
    @validator("due_date")
    def due_date_must_be_future(cls, v):
        """
        Validate that the due date is in the future.
        """
        if v and v < date.today():
            raise ValueError("Due date must be in the future")
        return v


class ContentPieceRead(ContentPieceBase, BaseModel):
    """
    Schema for reading content piece data.
    """
    id: int
    client_id: int
    review_comment: Optional[str] = None
    published_at: Optional[datetime] = None 
    client_rating: Optional[float] = None # Add client_rating
    created_at: datetime
    updated_at: Optional[datetime] = None


class ContentPieceUpdate(SQLModel):
    """
    Schema for updating a content piece.
    """
    title: Optional[str] = None
    idea: Optional[str] = None
    angle: Optional[str] = None
    content_body: Optional[str] = None
    status: Optional[ContentStatus] = None
    due_date: Optional[date] = None
    is_active: Optional[bool] = None
    review_comment: Optional[str] = None
    published_at: Optional[datetime] = None # Add published_at (likely read-only via update)
    
    @validator("due_date")
    def due_date_must_be_future(cls, v):
        """
        Validate that the due date is in the future.
        """
        if v and v < date.today():
            raise ValueError("Due date must be in the future")
        return v

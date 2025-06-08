"""
Content model module.

This module contains the ContentPiece model and related schemas.
"""
from typing import Optional, List, TYPE_CHECKING, Dict, Any
from datetime import date, datetime, timezone
from enum import Enum, auto

from pydantic import validator
from sqlmodel import Field, SQLModel, Relationship, Column, Float, TEXT, JSON
from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import JSONB

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
    SCHEDULED = "SCHEDULED"
    PUBLISHED = "PUBLISHED"


class ContentPieceBase(SQLModel):
    """
    Base model for ContentPiece with common fields.
    """
    client_id: int = Field(foreign_key="client.id", index=True)
    title: str
    idea: str = Field(default="")
    angle: str = Field(default="")
    content_body: str = Field(sa_type=TEXT)
    status: ContentStatus = Field(default=ContentStatus.DRAFT, index=True)
    due_date: Optional[datetime] = Field(default=None, index=True)
    scheduled_at: Optional[datetime] = Field(default=None, index=True)
    review_comment: Optional[str] = Field(default=None)
    client_rating: Optional[float] = Field(default=None)
    is_active: bool = Field(default=True)
    attachments: Optional[List[str]] = Field(default=None, sa_column=Column(JSONB))

    def __init__(self, **data):
        super().__init__(**data)
        # Convert scheduled_at to UTC if it has timezone info
        if self.scheduled_at and self.scheduled_at.tzinfo is not None:
            self.scheduled_at = self.scheduled_at.astimezone(timezone.utc)
        elif self.scheduled_at:
            self.scheduled_at = self.scheduled_at.replace(tzinfo=timezone.utc)


class ContentPiece(BaseModel, ContentPieceBase, TimestampMixin, table=True):
    """
    ContentPiece model for database.
    
    This model represents a content piece in the system, which is linked to a client profile.
    """
    # Foreign key to ClientProfile
    client_id: int = Field(foreign_key="clientprofile.id")
    
    # Optional published timestamp
    published_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    
    # Attachments field
    attachments: Optional[List[str]] = Field(default=None, sa_column=Column(JSONB))
    
    # LinkedIn media assets
    linkedin_media_assets: Optional[List[Dict[str, Any]]] = Field(default=None, sa_column=Column(JSONB))
    
    # Relationships
    client_profile: "ClientProfile" = Relationship(back_populates="content_pieces")

    def __init__(self, **data):
        super().__init__(**data)
        # Convert attachments to list if it's a string
        if isinstance(self.attachments, str):
            try:
                import json
                self.attachments = json.loads(self.attachments)
            except:
                self.attachments = [self.attachments]
        
        # Convert linkedin_media_assets to list if it's a string
        if isinstance(self.linkedin_media_assets, str):
            try:
                import json
                self.linkedin_media_assets = json.loads(self.linkedin_media_assets)
            except:
                self.linkedin_media_assets = [self.linkedin_media_assets]


class ContentPieceCreate(ContentPieceBase):
    """
    Schema for creating a new content piece.
    """
    client_id: int
    attachments: Optional[List[str]] = None
    
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
    client_rating: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None
    attachments: Optional[List[str]] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S") if v else None
        }

    @validator('attachments', pre=True)
    def parse_attachments(cls, v):
        if isinstance(v, str):
            try:
                import json
                return json.loads(v)
            except:
                return [v]
        return v


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
    published_at: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None
    attachments: Optional[List[str]] = None
    
    @validator("due_date")
    def due_date_must_be_future(cls, v):
        """
        Validate that the due date is in the future.
        """
        if v and v < date.today():
            raise ValueError("Due date must be in the future")
        return v

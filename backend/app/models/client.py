"""
Client model module.

This module contains the ClientProfile model and related schemas.
"""
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

from pydantic import validator, EmailStr # Remove HttpUrl import
from sqlmodel import Field, SQLModel, Relationship

from app.models.base import BaseModel, TimestampMixin
from app.models.user import User

if TYPE_CHECKING:
    from app.models.strategy import Strategy
    from app.models.content import ContentPiece


class ClientProfileBase(SQLModel):
    """
    Base model for ClientProfile with common fields.
    """
    company_name: str = Field(index=True)
    industry: str
    website: Optional[str] = None # Revert to str
    linkedin_url: Optional[str] = None # Revert to str
    description: Optional[str] = None
    logo_url: Optional[str] = None # Revert to str
    is_active: bool = Field(default=True)


class ClientProfile(BaseModel, ClientProfileBase, TimestampMixin, table=True):
    """
    ClientProfile model for database.
    
    This model represents a client profile in the system, which is linked to a user
    with the CLIENT role.
    """
    # Foreign key to User
    user_id: int = Field(foreign_key="user.id")
    
    # Relationships
    user: User = Relationship(back_populates="client_profile")
    strategy: Optional["Strategy"] = Relationship(back_populates="client_profile")
    content_pieces: List["ContentPiece"] = Relationship(back_populates="client_profile")


class ClientProfileCreate(ClientProfileBase):
    """
    Schema for creating a new client profile AND its associated user.
    Includes user details needed for user creation.
    """
    # User details needed for creation
    email: EmailStr 
    password: str 
    full_name: Optional[str] = None
    
    # No user_id here, it's generated during creation.
    # Remove the old validator for user_id
    # @validator("user_id")
    def user_must_exist(cls, v, values, **kwargs):
        """
        Validate that the user exists and has the CLIENT role.
        
        Note: This validation is performed at the API level, not here.
        """
        return v


class ClientProfileRead(ClientProfileBase, BaseModel):
    """
    Schema for reading client profile data.
    """
    user_id: int


class ClientProfileUpdate(SQLModel):
    """
    Schema for updating a client profile.
    """
    company_name: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    is_active: Optional[bool] = None

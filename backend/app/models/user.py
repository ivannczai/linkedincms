"""
User model module.

This module contains the User model and related schemas.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, TYPE_CHECKING

from pydantic import EmailStr, validator
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import String # Import String type

from app.models.base import BaseModel, TimestampMixin

if TYPE_CHECKING:
    from app.models.client import ClientProfile


class UserRole(str, Enum):
    """
    Enum for user roles.
    """
    ADMIN = "admin"
    CLIENT = "client"


class UserBase(SQLModel):
    """
    Base model for User with common fields.
    """
    # Explicitly map EmailStr to SQLAlchemy String type
    email: EmailStr = Field(unique=True, index=True, sa_type=String(255))
    full_name: str
    role: UserRole = Field(default=UserRole.CLIENT)
    is_active: bool = Field(default=True)


class User(BaseModel, UserBase, TimestampMixin, table=True):
    """
    User model for database.

    This model represents a user in the system, which can be either an admin
    or a client. Includes fields for LinkedIn integration.
    """
    hashed_password: str
    last_login: Optional[datetime] = Field(default=None)

    # LinkedIn Integration Fields
    linkedin_id: Optional[str] = Field(default=None, unique=True, index=True)
    linkedin_access_token: Optional[str] = Field(default=None) # Consider encrypting this field
    linkedin_token_expires_at: Optional[datetime] = Field(default=None)
    linkedin_scopes: Optional[str] = Field(default=None) # Store space-separated scopes

    # Relationships
    client_profile: Optional["ClientProfile"] = Relationship(back_populates="user", sa_relationship_kwargs={"uselist": False})


class UserCreate(UserBase):
    """
    Schema for creating a new user.
    """
    password: str

    @validator("password")
    def password_min_length(cls, v):
        """
        Validate that password meets minimum length requirement.
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class UserRead(UserBase, BaseModel):
    """
    Schema for reading user data, including LinkedIn ID.
    Excludes sensitive fields like password and access token.
    """
    # Inherits id, created_at, updated_at from BaseModel
    # Inherits email, full_name, role, is_active from UserBase
    last_login: Optional[datetime] = None
    linkedin_id: Optional[str] = None
    # Do NOT include linkedin_access_token or linkedin_token_expires_at here for security


class UserUpdate(SQLModel):
    """
    Schema for updating a user.
    """
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

    @validator("password")
    def password_min_length(cls, v):
        """
        Validate that password meets minimum length requirement.
        """
        if v is not None and len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v

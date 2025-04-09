"""
Base models module.

This module contains base models and mixins used across the application.
"""
from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class TimestampMixin(SQLModel):
    """
    Mixin that adds created_at and updated_at fields to a model.
    """
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: Optional[datetime] = Field(default=None, index=True)


class BaseModel(SQLModel):
    """
    Base model with ID field.
    """
    id: Optional[int] = Field(default=None, primary_key=True)

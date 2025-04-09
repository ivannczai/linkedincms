"""
Strategy model module.

This module contains the Strategy model and related schemas.
"""
from typing import Optional, TYPE_CHECKING
from datetime import datetime

from sqlmodel import Field, SQLModel, Relationship

from app.models.base import BaseModel, TimestampMixin

if TYPE_CHECKING:
    from app.models.client import ClientProfile


class StrategyBase(SQLModel):
    """
    Base model for Strategy with common fields.
    """
    title: str = Field(index=True)
    details: str
    is_active: bool = Field(default=True)


class Strategy(BaseModel, StrategyBase, TimestampMixin, table=True):
    """
    Strategy model for database.
    
    This model represents a content strategy for a client profile.
    It contains detailed information about the client's content strategy
    in Markdown format.
    """
    # Foreign key to ClientProfile
    client_id: int = Field(foreign_key="clientprofile.id")
    
    # Relationships
    client_profile: Optional["ClientProfile"] = Relationship(back_populates="strategy")


class StrategyCreate(StrategyBase):
    """
    Schema for creating a new strategy.
    """
    client_id: int


class StrategyRead(StrategyBase, BaseModel):
    """
    Schema for reading strategy data.
    """
    client_id: int


class StrategyUpdate(SQLModel):
    """
    Schema for updating a strategy.
    """
    title: Optional[str] = None
    details: Optional[str] = None
    is_active: Optional[bool] = None

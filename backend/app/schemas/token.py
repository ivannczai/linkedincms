"""
Token schemas module.

This module contains schemas for authentication tokens.
"""
from typing import Optional

from pydantic import BaseModel

from app.models.user import UserRole


class Token(BaseModel):
    """
    Schema for access token.
    """
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """
    Schema for token payload.
    """
    sub: Optional[int] = None
    exp: Optional[int] = None


class TokenData(BaseModel):
    """
    Schema for token data.
    """
    user_id: int
    role: UserRole

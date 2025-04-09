"""
Tests for security module.
"""
from datetime import datetime, timedelta

from jose import jwt

from app.core.config import settings
from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)


def test_password_hash():
    """
    Test password hashing and verification.
    """
    password = "testpassword123"
    hashed = get_password_hash(password)
    
    # Hashed password should be different from original
    assert hashed != password
    
    # Verification should work
    assert verify_password(password, hashed)
    
    # Wrong password should not verify
    assert not verify_password("wrongpassword", hashed)


def test_create_access_token():
    """
    Test JWT token creation.
    """
    # Create token with default expiry
    token = create_access_token(subject=1)
    
    # Decode and verify token
    payload = jwt.decode(
        token, settings.SECRET_KEY, algorithms=["HS256"]
    )
    
    # Check payload
    assert payload["sub"] == "1"
    assert "exp" in payload
    
    # Create token with custom expiry
    expires = timedelta(minutes=30)
    token = create_access_token(subject=2, expires_delta=expires)
    
    # Decode and verify token
    payload = jwt.decode(
        token, settings.SECRET_KEY, algorithms=["HS256"]
    )
    
    # Check payload
    assert payload["sub"] == "2"
    assert "exp" in payload
    
    # Expiry should be approximately 30 minutes from now
    exp_time = datetime.fromtimestamp(payload["exp"])
    now = datetime.utcnow()
    diff = exp_time - now
    assert abs(diff.total_seconds() - expires.total_seconds()) < 10  # Allow small difference

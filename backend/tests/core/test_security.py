"""
Tests for security utilities.
"""
from datetime import timedelta, datetime, timezone # Import timezone
from jose import jwt

from app.core.config import settings
from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
    encrypt_data,
    decrypt_data
)


def test_password_hashing():
    """
    Test password hashing and verification.
    """
    password = "password123"
    hashed_password = get_password_hash(password)

    # Check that hash is different from original password
    assert password != hashed_password

    # Check that verification works
    assert verify_password(password, hashed_password) is True
    assert verify_password("wrongpassword", hashed_password) is False


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
    # Use timezone-aware datetime for comparison
    exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    now = datetime.now(timezone.utc) # Use timezone-aware now
    diff = exp_time - now
    # Allow a small difference (e.g., 10 seconds) for processing time
    assert abs(diff.total_seconds() - expires.total_seconds()) < 10


def test_data_encryption_decryption():
    """
    Test data encryption and decryption.
    """
    original_data = "my_secret_linkedin_token"
    encrypted_data = encrypt_data(original_data)

    # Check encrypted data is different
    assert original_data != encrypted_data
    # Check it's a string (likely base64 encoded)
    assert isinstance(encrypted_data, str)

    # Check decryption works
    decrypted_data = decrypt_data(encrypted_data)
    assert decrypted_data == original_data

    # Test decryption with invalid token
    invalid_encrypted_data = encrypted_data[:-5] + "xxxxx" # Tamper with the data
    decrypted_invalid = decrypt_data(invalid_encrypted_data)
    assert decrypted_invalid is None

    # Test decrypting None or empty string
    assert decrypt_data(None) is None
    assert decrypt_data("") is None

    # Test encrypting None or empty string
    assert encrypt_data("") == ""
    # Depending on implementation, encrypting None might raise error or return None/empty
    # Assuming it should handle empty string gracefully as above. If None is passed,
    # the current implementation might raise an error due to encode(), adjust if needed.
    # assert encrypt_data(None) is None # Or check for expected error

"""
Security related utilities.

Includes password hashing, token creation/verification, and data encryption.
"""
import base64
from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional

from jose import jwt
from jose.exceptions import JWTError
from passlib.context import CryptContext
from cryptography.fernet import Fernet, InvalidToken # Import Fernet and InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Encryption Setup ---
# Derive a stable encryption key from the SECRET_KEY using PBKDF2
# WARNING: Changing SECRET_KEY will make previously encrypted data unrecoverable!
# Use a static salt or store it securely if needed across restarts/deployments
# For simplicity here, using a hardcoded salt (NOT RECOMMENDED FOR HIGH SECURITY)
_SALT = b'qN38_Tr!z9-f$5@L' # Replace with a securely generated and stored salt in production
_kdf = PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=32,
    salt=_SALT,
    iterations=480000, # Adjust iterations as needed for performance/security balance
)
_ENCRYPTION_KEY = base64.urlsafe_b64encode(_kdf.derive(settings.SECRET_KEY.encode()))
_fernet = Fernet(_ENCRYPTION_KEY)

def encrypt_data(data: str) -> str:
    """Encrypts a string using Fernet."""
    if not data:
        return data
    try:
        return _fernet.encrypt(data.encode()).decode()
    except Exception as e:
        # Log encryption error
        print(f"Encryption failed: {e}")
        raise ValueError("Data encryption failed") from e

def decrypt_data(encrypted_data: str) -> Optional[str]:
    """Decrypts a string using Fernet. Returns None if decryption fails."""
    if not encrypted_data:
        return None
    try:
        return _fernet.decrypt(encrypted_data.encode()).decode()
    except InvalidToken:
        # Log decryption error (e.g., invalid token, key mismatch)
        print(f"Decryption failed: Invalid token or key")
        return None
    except Exception as e:
        # Log other decryption errors
        print(f"Decryption failed: {e}")
        return None

# --- Password Hashing ---
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a plain password."""
    return pwd_context.hash(password)

# --- JWT Token Handling ---
ALGORITHM = "HS256"

def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=ALGORITHM
    )
    return encoded_jwt

# Note: Token verification happens within the get_current_user dependency

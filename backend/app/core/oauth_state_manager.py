"""
Manages temporary storage and verification of OAuth 2.0 state parameters.

This implementation uses a simple in-memory dictionary with timestamps for expiry,
suitable for single-instance development environments. For production or multi-instance
deployments, consider using a more robust solution like Redis or a database table.
"""

import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Tuple

# Store state -> (user_id, expiry_timestamp)
_state_storage: Dict[str, Tuple[int, float]] = {}
_STATE_EXPIRY_SECONDS = 300  # 5 minutes


def generate_state() -> str:
    """Generates a secure random string for the state parameter."""
    return secrets.token_urlsafe(32)


def store_state(state: str, user_id: int) -> None:
    """
    Stores the state parameter linked to a user ID with an expiry time.

    Args:
        state: The state string to store.
        user_id: The ID of the user initiating the OAuth flow.
    """
    expiry = time.time() + _STATE_EXPIRY_SECONDS
    _state_storage[state] = (user_id, expiry)
    _cleanup_expired_states() # Clean up old states occasionally


def verify_and_consume_state(received_state: str) -> Optional[int]:
    """
    Verifies the received state parameter, returns the associated user ID if valid
    and not expired, and removes the state from storage.

    Args:
        received_state: The state parameter received from the OAuth callback.

    Returns:
        The user ID associated with the state if valid and not expired, otherwise None.
    """
    _cleanup_expired_states() # Ensure expired states are removed before check

    if received_state in _state_storage:
        user_id, expiry = _state_storage[received_state]
        if time.time() < expiry:
            # Valid state, consume it (remove from storage)
            del _state_storage[received_state]
            return user_id
        else:
            # Expired state, remove it
            del _state_storage[received_state]
            return None
    return None


def _cleanup_expired_states() -> None:
    """Removes expired states from the in-memory storage."""
    now = time.time()
    expired_keys = [
        state for state, (_, expiry) in _state_storage.items() if expiry < now
    ]
    for key in expired_keys:
        try:
            del _state_storage[key]
        except KeyError:
            # Might have been deleted by another concurrent cleanup/verification
            pass

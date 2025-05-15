"""
Manages temporary storage and verification of OAuth 2.0 state parameters.

This implementation uses a simple in-memory dictionary with timestamps for expiry,
suitable for single-instance development environments. For production or multi-instance
deployments, consider using a more robust solution like Redis or a database table.
"""

import secrets
import time
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Tuple

logger = logging.getLogger(__name__)

# Store state -> (user_id, expiry_timestamp)
_state_storage: Dict[str, Tuple[int, float]] = {}
_STATE_EXPIRY_SECONDS = 600  # 10 minutes


def generate_state() -> str:
    """Generates a secure random string for the state parameter."""
    state = secrets.token_urlsafe(32)
    logger.info(f"Generated new state: {state}")
    return state


def store_state(state: str, user_id: int) -> None:
    """
    Stores the state parameter linked to a user ID with an expiry time.

    Args:
        state: The state string to store.
        user_id: The ID of the user initiating the OAuth flow.
    """
    expiry = time.time() + _STATE_EXPIRY_SECONDS
    _state_storage[state] = (user_id, expiry)
    logger.info(f"Stored state {state} for user {user_id}, expires at {datetime.fromtimestamp(expiry)}")
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
    logger.info(f"Verifying state: {received_state}")
    logger.info(f"Current states in storage: {_state_storage}")

    if received_state in _state_storage:
        user_id, expiry = _state_storage[received_state]
        current_time = time.time()
        logger.info(f"Found state for user {user_id}, expires at {datetime.fromtimestamp(expiry)}, current time: {datetime.fromtimestamp(current_time)}")
        
        if current_time < expiry:
            # Valid state, consume it (remove from storage)
            del _state_storage[received_state]
            logger.info(f"State valid, consumed and removed from storage")
            return user_id
        else:
            # Expired state, remove it
            del _state_storage[received_state]
            logger.warning(f"State expired, removed from storage")
            return None
    logger.warning(f"State not found in storage")
    return None


def clear_user_states(user_id: int) -> None:
    """
    Clears all OAuth states for a specific user.

    Args:
        user_id: The ID of the user whose states should be cleared.
    """
    global _state_storage
    old_states = _state_storage
    _state_storage = {
        state: (uid, expiry) 
        for state, (uid, expiry) in _state_storage.items() 
        if uid != user_id
    }
    logger.info(f"Cleared states for user {user_id}. Old states: {old_states}, New states: {_state_storage}")


def _cleanup_expired_states() -> None:
    """Removes expired states from the in-memory storage."""
    now = time.time()
    expired_keys = [
        state for state, (_, expiry) in _state_storage.items() if expiry < now
    ]
    if expired_keys:
        logger.info(f"Cleaning up {len(expired_keys)} expired states: {expired_keys}")
    for key in expired_keys:
        try:
            del _state_storage[key]
        except KeyError:
            # Might have been deleted by another concurrent cleanup/verification
            pass

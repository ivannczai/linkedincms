"""
Tests for user CRUD operations.
"""
from sqlmodel import Session

from app.crud.user import (
    authenticate,
    create,
    get,
    get_by_email,
    is_active,
    is_admin,
    update,
)
from app.models.user import User, UserCreate, UserRole, UserUpdate


def test_create_user(session: Session):
    """
    Test creating a user.
    """
    # Create user data
    user_in = UserCreate(
        email="test@example.com",
        password="password123",
        full_name="Test User",
        role=UserRole.CLIENT,
    )
    
    # Create user
    user = create(session, user_in)
    
    # Check user
    assert user.email == user_in.email
    assert user.full_name == user_in.full_name
    assert user.role == user_in.role
    assert user.is_active
    assert hasattr(user, "hashed_password")
    assert user.hashed_password != user_in.password  # Password should be hashed


def test_get_user(session: Session):
    """
    Test getting a user by ID.
    """
    # Create user
    user_in = UserCreate(
        email="test@example.com",
        password="password123",
        full_name="Test User",
        role=UserRole.CLIENT,
    )
    user = create(session, user_in)
    
    # Get user
    retrieved_user = get(session, user.id)
    
    # Check user
    assert retrieved_user is not None
    assert retrieved_user.id == user.id
    assert retrieved_user.email == user.email


def test_get_user_by_email(session: Session):
    """
    Test getting a user by email.
    """
    # Create user
    user_in = UserCreate(
        email="test@example.com",
        password="password123",
        full_name="Test User",
        role=UserRole.CLIENT,
    )
    user = create(session, user_in)
    
    # Get user by email
    retrieved_user = get_by_email(session, user.email)
    
    # Check user
    assert retrieved_user is not None
    assert retrieved_user.id == user.id
    assert retrieved_user.email == user.email


def test_update_user(session: Session):
    """
    Test updating a user.
    """
    # Create user
    user_in = UserCreate(
        email="test@example.com",
        password="password123",
        full_name="Test User",
        role=UserRole.CLIENT,
    )
    user = create(session, user_in)
    
    # Update user
    user_update = UserUpdate(
        full_name="Updated User",
        password="newpassword123",
    )
    updated_user = update(session, user, user_update)
    
    # Check updated user
    assert updated_user.id == user.id
    assert updated_user.email == user.email  # Email should not change
    assert updated_user.full_name == user_update.full_name
    assert updated_user.hashed_password != user.hashed_password  # Password should be updated


def test_authenticate_user(session: Session):
    """
    Test authenticating a user.
    """
    # Create user
    user_in = UserCreate(
        email="test@example.com",
        password="password123",
        full_name="Test User",
        role=UserRole.CLIENT,
    )
    create(session, user_in)
    
    # Authenticate with correct credentials
    authenticated_user = authenticate(session, user_in.email, user_in.password)
    assert authenticated_user is not None
    assert authenticated_user.email == user_in.email
    
    # Authenticate with wrong password
    authenticated_user = authenticate(session, user_in.email, "wrongpassword")
    assert authenticated_user is None
    
    # Authenticate with wrong email
    authenticated_user = authenticate(session, "wrong@example.com", user_in.password)
    assert authenticated_user is None


def test_is_active_user(session: Session):
    """
    Test checking if a user is active.
    """
    # Create active user
    active_user_in = UserCreate(
        email="active@example.com",
        password="password123",
        full_name="Active User",
        role=UserRole.CLIENT,
        is_active=True,
    )
    active_user = create(session, active_user_in)
    
    # Create inactive user
    inactive_user_in = UserCreate(
        email="inactive@example.com",
        password="password123",
        full_name="Inactive User",
        role=UserRole.CLIENT,
        is_active=False,
    )
    inactive_user = create(session, inactive_user_in)
    
    # Check active status
    assert is_active(active_user)
    assert not is_active(inactive_user)


def test_is_admin_user(session: Session):
    """
    Test checking if a user is an admin.
    """
    # Create admin user
    admin_user_in = UserCreate(
        email="admin@example.com",
        password="password123",
        full_name="Admin User",
        role=UserRole.ADMIN,
    )
    admin_user = create(session, admin_user_in)
    
    # Create client user
    client_user_in = UserCreate(
        email="client@example.com",
        password="password123",
        full_name="Client User",
        role=UserRole.CLIENT,
    )
    client_user = create(session, client_user_in)
    
    # Check admin status
    assert is_admin(admin_user)
    assert not is_admin(client_user)

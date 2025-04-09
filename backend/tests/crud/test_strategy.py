"""
Tests for strategy CRUD operations.
"""
import pytest
from sqlmodel import Session

from app.crud.strategy import (
    create,
    delete,
    get,
    get_by_client_id,
    get_multi,
    update,
)
from app.crud.client import create as create_client
from app.crud.user import create as create_user
from app.models.strategy import Strategy, StrategyCreate, StrategyUpdate
from app.models.client import ClientProfileCreate
from app.models.user import UserCreate, UserRole


def test_create_strategy(session: Session):
    """
    Test creating a strategy.
    """
    # Create a client user first
    user_in = UserCreate(
        email="client@example.com",
        password="password123",
        full_name="Client User",
        role=UserRole.CLIENT,
    )
    user = create_user(session, user_in)
    
    # Create client profile
    client_in = ClientProfileCreate(
        user_id=user.id,
        company_name="Test Company",
        industry="Technology",
    )
    client = create_client(session, obj_in=client_in)
    
    # Create strategy
    strategy_in = StrategyCreate(
        client_id=client.id,
        title="Content Strategy 2025",
        details="# Content Strategy\n\nThis is a test strategy with Markdown content.",
    )
    strategy = create(session, obj_in=strategy_in)
    
    # Check strategy
    assert strategy.client_id == client.id
    assert strategy.title == strategy_in.title
    assert strategy.details == strategy_in.details
    assert strategy.is_active is True


def test_create_strategy_invalid_client(session: Session):
    """
    Test creating a strategy with an invalid client ID.
    """
    # Create strategy with non-existent client ID
    strategy_in = StrategyCreate(
        client_id=999,
        title="Content Strategy 2025",
        details="# Content Strategy\n\nThis is a test strategy with Markdown content.",
    )
    
    # Should raise ValueError
    with pytest.raises(ValueError, match=f"Client with ID {strategy_in.client_id} not found"):
        create(session, obj_in=strategy_in)


def test_get_strategy(session: Session):
    """
    Test getting a strategy by ID.
    """
    # Create a client user
    user_in = UserCreate(
        email="client@example.com",
        password="password123",
        full_name="Client User",
        role=UserRole.CLIENT,
    )
    user = create_user(session, user_in)
    
    # Create client profile
    client_in = ClientProfileCreate(
        user_id=user.id,
        company_name="Test Company",
        industry="Technology",
    )
    client = create_client(session, obj_in=client_in)
    
    # Create strategy
    strategy_in = StrategyCreate(
        client_id=client.id,
        title="Content Strategy 2025",
        details="# Content Strategy\n\nThis is a test strategy with Markdown content.",
    )
    strategy = create(session, obj_in=strategy_in)
    
    # Get strategy
    retrieved_strategy = get(session, strategy.id)
    
    # Check strategy
    assert retrieved_strategy is not None
    assert retrieved_strategy.id == strategy.id
    assert retrieved_strategy.client_id == strategy.client_id
    assert retrieved_strategy.title == strategy.title


def test_get_by_client_id(session: Session):
    """
    Test getting a strategy by client ID.
    """
    # Create a client user
    user_in = UserCreate(
        email="client@example.com",
        password="password123",
        full_name="Client User",
        role=UserRole.CLIENT,
    )
    user = create_user(session, user_in)
    
    # Create client profile
    client_in = ClientProfileCreate(
        user_id=user.id,
        company_name="Test Company",
        industry="Technology",
    )
    client = create_client(session, obj_in=client_in)
    
    # Create strategy
    strategy_in = StrategyCreate(
        client_id=client.id,
        title="Content Strategy 2025",
        details="# Content Strategy\n\nThis is a test strategy with Markdown content.",
    )
    strategy = create(session, obj_in=strategy_in)
    
    # Get strategy by client ID
    retrieved_strategy = get_by_client_id(session, client.id)
    
    # Check strategy
    assert retrieved_strategy is not None
    assert retrieved_strategy.id == strategy.id
    assert retrieved_strategy.client_id == client.id


def test_get_multi(session: Session):
    """
    Test getting multiple strategies.
    """
    # Create client users
    user_in1 = UserCreate(
        email="client1@example.com",
        password="password123",
        full_name="Client User 1",
        role=UserRole.CLIENT,
    )
    user1 = create_user(session, user_in1)
    
    user_in2 = UserCreate(
        email="client2@example.com",
        password="password123",
        full_name="Client User 2",
        role=UserRole.CLIENT,
    )
    user2 = create_user(session, user_in2)
    
    # Create client profiles
    client_in1 = ClientProfileCreate(
        user_id=user1.id,
        company_name="Test Company 1",
        industry="Technology",
    )
    client1 = create_client(session, obj_in=client_in1)
    
    client_in2 = ClientProfileCreate(
        user_id=user2.id,
        company_name="Test Company 2",
        industry="Finance",
    )
    client2 = create_client(session, obj_in=client_in2)
    
    # Create strategies
    strategy_in1 = StrategyCreate(
        client_id=client1.id,
        title="Content Strategy 2025 - Tech",
        details="# Technology Content Strategy",
    )
    strategy1 = create(session, obj_in=strategy_in1)
    
    strategy_in2 = StrategyCreate(
        client_id=client2.id,
        title="Content Strategy 2025 - Finance",
        details="# Finance Content Strategy",
        is_active=False,
    )
    strategy2 = create(session, obj_in=strategy_in2)
    
    # Get all strategies
    strategies = get_multi(session, active_only=False)
    assert len(strategies) == 2
    
    # Get active strategies only
    active_strategies = get_multi(session, active_only=True)
    assert len(active_strategies) == 1
    assert active_strategies[0].id == strategy1.id


def test_update_strategy(session: Session):
    """
    Test updating a strategy.
    """
    # Create a client user
    user_in = UserCreate(
        email="client@example.com",
        password="password123",
        full_name="Client User",
        role=UserRole.CLIENT,
    )
    user = create_user(session, user_in)
    
    # Create client profile
    client_in = ClientProfileCreate(
        user_id=user.id,
        company_name="Test Company",
        industry="Technology",
    )
    client = create_client(session, obj_in=client_in)
    
    # Create strategy
    strategy_in = StrategyCreate(
        client_id=client.id,
        title="Content Strategy 2025",
        details="# Content Strategy\n\nThis is a test strategy with Markdown content.",
    )
    strategy = create(session, obj_in=strategy_in)
    
    # Update strategy
    strategy_update = StrategyUpdate(
        title="Updated Content Strategy 2025",
        details="# Updated Content Strategy\n\nThis is an updated test strategy.",
    )
    updated_strategy = update(session, db_obj=strategy, obj_in=strategy_update)
    
    # Check updated strategy
    assert updated_strategy.id == strategy.id
    assert updated_strategy.title == strategy_update.title
    assert updated_strategy.details == strategy_update.details
    assert updated_strategy.client_id == strategy.client_id  # Should not change


def test_delete_strategy(session: Session):
    """
    Test deleting a strategy.
    """
    # Create a client user
    user_in = UserCreate(
        email="client@example.com",
        password="password123",
        full_name="Client User",
        role=UserRole.CLIENT,
    )
    user = create_user(session, user_in)
    
    # Create client profile
    client_in = ClientProfileCreate(
        user_id=user.id,
        company_name="Test Company",
        industry="Technology",
    )
    client = create_client(session, obj_in=client_in)
    
    # Create strategy
    strategy_in = StrategyCreate(
        client_id=client.id,
        title="Content Strategy 2025",
        details="# Content Strategy\n\nThis is a test strategy with Markdown content.",
    )
    strategy = create(session, obj_in=strategy_in)
    
    # Delete strategy
    deleted_strategy = delete(session, strategy_id=strategy.id)
    
    # Check deleted strategy
    assert deleted_strategy is not None
    assert deleted_strategy.id == strategy.id
    
    # Check that strategy is deleted
    retrieved_strategy = get(session, strategy.id)
    assert retrieved_strategy is None

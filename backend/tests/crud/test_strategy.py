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
# Removed unused user CRUD import: from app.crud.user import create as create_user
from app.models.strategy import Strategy, StrategyCreate, StrategyUpdate
from app.models.client import ClientProfileCreate
# Removed unused user model imports: from app.models.user import UserCreate, UserRole


def test_create_strategy(session: Session):
    """
    Test creating a strategy.
    """
    # Create client profile (which also creates the user)
    client_in = ClientProfileCreate(
        email="client.strat.crud@example.com",
        password="password123",
        full_name="Client User CRUD",
        company_name="Test Company CRUD",
        industry="Technology CRUD",
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

    # Should raise ValueError because client doesn't exist
    with pytest.raises(ValueError, match=f"Client with ID {strategy_in.client_id} not found"):
        create(session, obj_in=strategy_in)


def test_get_strategy(session: Session):
    """
    Test getting a strategy by ID.
    """
    # Create client profile
    client_in = ClientProfileCreate(
        email="client.get.strat@example.com",
        password="password123",
        full_name="Client Get Strat",
        company_name="Test Get Company",
        industry="Technology Get",
    )
    client = create_client(session, obj_in=client_in)

    # Create strategy
    strategy_in = StrategyCreate(
        client_id=client.id,
        title="Content Strategy Get",
        details="# Content Strategy Get",
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
    # Create client profile
    client_in = ClientProfileCreate(
        email="client.getbyid.strat@example.com",
        password="password123",
        full_name="Client GetByID Strat",
        company_name="Test GetByID Company",
        industry="Technology GetByID",
    )
    client = create_client(session, obj_in=client_in)

    # Create strategy
    strategy_in = StrategyCreate(
        client_id=client.id,
        title="Content Strategy GetByID",
        details="# Content Strategy GetByID",
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
    # Create client profiles
    client_in1 = ClientProfileCreate(
        email="client.multi1.strat@example.com",
        password="password123",
        full_name="Client Multi1 Strat",
        company_name="Test Multi1 Company",
        industry="Technology Multi1",
    )
    client1 = create_client(session, obj_in=client_in1)

    client_in2 = ClientProfileCreate(
        email="client.multi2.strat@example.com",
        password="password123",
        full_name="Client Multi2 Strat",
        company_name="Test Multi2 Company",
        industry="Finance Multi2",
    )
    client2 = create_client(session, obj_in=client_in2)

    # Create strategies
    strategy_in1 = StrategyCreate(
        client_id=client1.id,
        title="Content Strategy Multi1",
        details="# Technology Content Strategy Multi1",
    )
    strategy1 = create(session, obj_in=strategy_in1)

    strategy_in2 = StrategyCreate(
        client_id=client2.id,
        title="Content Strategy Multi2",
        details="# Finance Content Strategy Multi2",
        is_active=False, # Create one inactive
    )
    strategy2 = create(session, obj_in=strategy_in2)

    # Get all strategies
    strategies = get_multi(session, active_only=False)
    assert len(strategies) >= 2 # Use >= in case other tests left data

    # Get active strategies only
    active_strategies = get_multi(session, active_only=True)
    # Filter results to find the specific active strategy created in this test
    found_active = any(s.id == strategy1.id for s in active_strategies)
    found_inactive = any(s.id == strategy2.id for s in active_strategies)
    assert found_active is True
    assert found_inactive is False


def test_update_strategy(session: Session):
    """
    Test updating a strategy.
    """
    # Create client profile
    client_in = ClientProfileCreate(
        email="client.update.strat@example.com",
        password="password123",
        full_name="Client Update Strat",
        company_name="Test Update Company",
        industry="Technology Update",
    )
    client = create_client(session, obj_in=client_in)

    # Create strategy
    strategy_in = StrategyCreate(
        client_id=client.id,
        title="Content Strategy Update",
        details="# Content Strategy Update",
    )
    strategy = create(session, obj_in=strategy_in)

    # Update strategy
    strategy_update = StrategyUpdate(
        title="Updated Content Strategy",
        details="# Updated Content Strategy Details",
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
    # Create client profile
    client_in = ClientProfileCreate(
        email="client.delete.strat@example.com",
        password="password123",
        full_name="Client Delete Strat",
        company_name="Test Delete Company",
        industry="Technology Delete",
    )
    client = create_client(session, obj_in=client_in)

    # Create strategy
    strategy_in = StrategyCreate(
        client_id=client.id,
        title="Content Strategy Delete",
        details="# Content Strategy Delete",
    )
    strategy = create(session, obj_in=strategy_in)
    strategy_id = strategy.id # Store ID

    # Delete strategy
    deleted_strategy = delete(session, strategy_id=strategy_id)

    # Check deleted strategy
    assert deleted_strategy is not None
    assert deleted_strategy.id == strategy_id

    # Check that strategy is deleted
    retrieved_strategy = get(session, strategy_id)
    assert retrieved_strategy is None

"""
Tests for client CRUD operations.
"""
import pytest
from sqlmodel import Session
from fastapi import HTTPException

from app.crud.client import (
    create,
    delete,
    get,
    get_by_user_id,
    get_multi,
    update,
)
from app.crud.user import get as get_user # Need get_user to verify user creation
from app.models.client import ClientProfile, ClientProfileCreate, ClientProfileUpdate
from app.models.user import User, UserRole # Keep User import


def test_create_client(session: Session):
    """
    Test creating a client profile and its associated user.
    """
    client_in = ClientProfileCreate(
        email="newclient.crud@example.com", # Use unique email for test
        password="password123",
        full_name="CRUD Client User",
        company_name="CRUD Test Company",
        industry="Testing",
        website="https://crudtest.com",
        linkedin_url="https://linkedin.com/company/crudtest",
        description="A CRUD test company",
    )
    client_profile = create(session, obj_in=client_in)
    
    # Check client profile
    assert client_profile.company_name == client_in.company_name
    assert client_profile.industry == client_in.industry
    assert str(client_profile.website) == client_in.website # Compare string representation
    assert str(client_profile.linkedin_url) == client_in.linkedin_url # Compare string representation
    assert client_profile.description == client_in.description
    assert client_profile.is_active is True
    assert client_profile.user_id is not None # Check user_id was assigned

    # Check associated user
    user = get_user(session, client_profile.user_id)
    assert user is not None
    assert user.email == client_in.email
    assert user.full_name == client_in.full_name
    assert user.role == UserRole.CLIENT
    assert user.is_active is True


def test_create_client_duplicate_email(session: Session):
    """
    Test creating a client with an email that already exists.
    """
    # Create initial client
    client_in_1 = ClientProfileCreate(
        email="duplicate.crud@example.com", 
        password="password123",
        company_name="Company 1",
        industry="Tech",
    )
    create(session, obj_in=client_in_1)

    # Attempt to create another client with the same email
    client_in_2 = ClientProfileCreate(
        email="duplicate.crud@example.com", 
        password="password456",
        company_name="Company 2",
        industry="Finance",
    )
    
    with pytest.raises(HTTPException) as excinfo:
        create(session, obj_in=client_in_2)
    assert excinfo.value.status_code == 400
    assert "email already exists" in excinfo.value.detail.lower()


# Removed test_create_client_invalid_user_role as it's no longer applicable


def test_get_client(session: Session):
    """
    Test getting a client profile by ID.
    """
    client_in = ClientProfileCreate(
        email="getclient.crud@example.com", 
        password="password123",
        company_name="Get Test Co",
        industry="Testing",
    )
    client = create(session, obj_in=client_in)
    
    retrieved_client = get(session, client.id)
    
    assert retrieved_client is not None
    assert retrieved_client.id == client.id
    assert retrieved_client.user_id == client.user_id
    assert retrieved_client.company_name == client.company_name


def test_get_by_user_id(session: Session):
    """
    Test getting a client profile by user ID.
    """
    client_in = ClientProfileCreate(
        email="getbyuser.crud@example.com", 
        password="password123",
        company_name="Get By User Test Co",
        industry="Testing",
    )
    client = create(session, obj_in=client_in)
    
    retrieved_client = get_by_user_id(session, client.user_id)
    
    assert retrieved_client is not None
    assert retrieved_client.id == client.id
    assert retrieved_client.user_id == client.user_id


def test_get_multi(session: Session):
    """
    Test getting multiple client profiles.
    """
    client_in1 = ClientProfileCreate(
        email="multi1.crud@example.com", 
        password="password123",
        company_name="Multi Test Co 1",
        industry="Tech",
    )
    client1 = create(session, obj_in=client_in1)
    
    client_in2 = ClientProfileCreate(
        email="multi2.crud@example.com", 
        password="password123",
        company_name="Multi Test Co 2",
        industry="Finance",
        is_active=False, # Create one inactive
    )
    client2 = create(session, obj_in=client_in2)
    
    # Get all client profiles
    clients = get_multi(session, active_only=False)
    assert len(clients) >= 2 # Use >= in case other tests left data
    
    # Get active client profiles only
    active_clients = get_multi(session, active_only=True)
    # Filter results to find the specific active client created in this test
    found_active = any(c.id == client1.id for c in active_clients)
    found_inactive = any(c.id == client2.id for c in active_clients)
    assert found_active is True
    assert found_inactive is False


def test_update_client(session: Session):
    """
    Test updating a client profile.
    """
    client_in = ClientProfileCreate(
        email="updateclient.crud@example.com", 
        password="password123",
        company_name="Update Test Co",
        industry="Testing",
    )
    client = create(session, obj_in=client_in)
    
    client_update = ClientProfileUpdate(
        company_name="Updated Company Name",
        website="https://updated.com",
    )
    updated_client = update(session, db_obj=client, obj_in=client_update)
    
    assert updated_client.id == client.id
    assert updated_client.company_name == client_update.company_name
    assert updated_client.industry == client.industry  # Should not change
    assert str(updated_client.website) == client_update.website # Compare string


def test_delete_client(session: Session):
    """
    Test deleting a client profile.
    """
    client_in = ClientProfileCreate(
        email="deleteclient.crud@example.com", 
        password="password123",
        company_name="Delete Test Co",
        industry="Testing",
    )
    client = create(session, obj_in=client_in)
    client_id = client.id # Store ID before deleting
    
    deleted_client = delete(session, client_id=client_id)
    
    assert deleted_client is not None
    assert deleted_client.id == client_id
    
    retrieved_client = get(session, client_id)
    assert retrieved_client is None

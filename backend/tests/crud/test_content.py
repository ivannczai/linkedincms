"""
Tests for content CRUD operations.
"""
import pytest
from sqlmodel import Session, select # Import select
from pydantic import ValidationError # Import Pydantic ValidationError
from fastapi import HTTPException, status
from datetime import date, datetime

from app.crud.content import (
    create,
    delete,
    get,
    get_multi,
    update,
    update_status,
    mark_as_posted,
    rate_content,
    ContentRatingInput
)
from app.crud.client import create as create_client_crud
from app.models.client import ClientProfile, ClientProfileCreate
from app.models.content import ContentPiece, ContentPieceCreate, ContentPieceUpdate, ContentStatus
from app.models.user import User, UserRole # Import User for rating test


# Helper function to create a client for tests
def create_test_client(session: Session, email: str = "client.content.test@example.com", company: str = "Content Test Co") -> ClientProfile:
    """Creates a client with profile and user for testing."""
    # Check if user already exists to prevent duplicate errors across tests
    existing_user = session.exec(select(User).where(User.email == email)).first()
    if existing_user:
        if not existing_user.client_profile:
             # If user exists but profile doesn't (unlikely state, but handle)
             client_in = ClientProfileCreate(
                 email=email, password="password123", full_name=f"User for {company}",
                 company_name=company, industry="Testing"
             )
             # Re-fetch the profile after creation if needed
             client_profile = create_client_crud(session, obj_in=client_in)
             existing_user.client_profile = client_profile # Manually link if necessary
             session.add(existing_user)
             session.commit()
             session.refresh(existing_user)
        # Ensure the user object has the profile linked for return
        if not hasattr(existing_user, 'client_profile') or existing_user.client_profile is None:
             # If still not linked, fetch the profile explicitly
             profile = session.exec(select(ClientProfile).where(ClientProfile.user_id == existing_user.id)).first()
             existing_user.client_profile = profile
        # Return the ClientProfile object associated with the user
        # Make sure the user object is attached to the profile for the test
        profile_to_return = existing_user.client_profile
        profile_to_return.user = existing_user
        return profile_to_return

    # If user doesn't exist, create them
    client_in = ClientProfileCreate(
        email=email,
        password="password123",
        full_name=f"User for {company}",
        company_name=company,
        industry="Testing",
    )
    client_profile = create_client_crud(session, obj_in=client_in)
    # Fetch the user associated with the created profile
    user = session.get(User, client_profile.user_id)
    if not user:
         # This should not happen if create_client_crud works correctly
         raise Exception(f"Failed to retrieve user after creating client profile for {email}")
    client_profile.user = user # Attach user for convenience
    return client_profile


def test_create_content(session: Session):
    """
    Test creating a content piece.
    """
    client = create_test_client(session)
    content_in = ContentPieceCreate(
        client_id=client.id,
        title="Test Content",
        idea="Test Idea",
        angle="Test Angle",
        content_body="Test Body",
        due_date=date.today().replace(year=date.today().year + 1) # Future date
    )
    content = create(session, obj_in=content_in)

    assert content.client_id == client.id
    assert content.title == content_in.title
    assert content.idea == content_in.idea
    assert content.angle == content_in.angle
    assert content.content_body == content_in.content_body
    assert content.status == ContentStatus.DRAFT
    assert content.due_date == content_in.due_date
    assert content.is_active is True
    assert content.review_comment is None
    assert content.published_at is None
    assert content.client_rating is None # Check new field


def test_get_content(session: Session):
    """
    Test getting a content piece by ID.
    """
    client = create_test_client(session)
    content_in = ContentPieceCreate(client_id=client.id, title="Get Test", idea="Idea", angle="Angle", content_body="Body")
    content = create(session, obj_in=content_in)

    retrieved_content = get(session, content.id)

    assert retrieved_content is not None
    assert retrieved_content.id == content.id
    assert retrieved_content.title == content.title


def test_get_multi_content(session: Session):
    """
    Test getting multiple content pieces with filters.
    """
    client1 = create_test_client(session, email="c1.multi.content@test.com", company="Multi Content Co 1")
    client2 = create_test_client(session, email="c2.multi.content@test.com", company="Multi Content Co 2")

    content1 = create(session, obj_in=ContentPieceCreate(client_id=client1.id, title="C1 Draft", idea="i", angle="a", content_body="b", status=ContentStatus.DRAFT))
    content2 = create(session, obj_in=ContentPieceCreate(client_id=client1.id, title="C1 Approved", idea="i", angle="a", content_body="b", status=ContentStatus.APPROVED))
    content3 = create(session, obj_in=ContentPieceCreate(client_id=client2.id, title="C2 Draft", idea="i", angle="a", content_body="b", status=ContentStatus.DRAFT))

    # Get all for client 1
    c1_contents = get_multi(session, client_id=client1.id)
    assert len(c1_contents) >= 2 # Adjust check due to potential existing data
    assert {c.id for c in c1_contents}.issuperset({content1.id, content2.id})

    # Get all drafts
    draft_contents = get_multi(session, status=ContentStatus.DRAFT)
    assert len(draft_contents) >= 2 # Adjust check
    assert {c.id for c in draft_contents}.issuperset({content1.id, content3.id})

    # Get all approved for client 1
    c1_approved = get_multi(session, client_id=client1.id, status=ContentStatus.APPROVED)
    assert len(c1_approved) >= 1 # Adjust check
    assert any(c.id == content2.id for c in c1_approved)


def test_update_content(session: Session):
    """
    Test updating a content piece.
    """
    client = create_test_client(session)
    content_in = ContentPieceCreate(client_id=client.id, title="Update Test", idea="i", angle="a", content_body="b")
    content = create(session, obj_in=content_in)

    update_data = ContentPieceUpdate(title="Updated Title", status=ContentStatus.PENDING_APPROVAL)
    updated_content = update(session, db_obj=content, obj_in=update_data)

    assert updated_content.id == content.id
    assert updated_content.title == update_data.title
    assert updated_content.status == update_data.status
    assert updated_content.idea == content.idea # Should not change


def test_delete_content(session: Session):
    """
    Test deleting a content piece.
    """
    client = create_test_client(session)
    content_in = ContentPieceCreate(client_id=client.id, title="Delete Test", idea="i", angle="a", content_body="b")
    content = create(session, obj_in=content_in)
    content_id = content.id

    deleted_content = delete(session, content_id=content_id)

    assert deleted_content is not None
    assert deleted_content.id == content_id

    retrieved_content = get(session, content_id)
    assert retrieved_content is None


def test_update_status(session: Session):
    """
    Test updating content status.
    """
    client = create_test_client(session)
    content = create(session, obj_in=ContentPieceCreate(client_id=client.id, title="Status Test", idea="i", angle="a", content_body="b"))

    # Draft -> Pending
    updated = update_status(session, content_id=content.id, new_status=ContentStatus.PENDING_APPROVAL)
    assert updated.status == ContentStatus.PENDING_APPROVAL

    # Pending -> Revision
    comment = "Needs more detail"
    updated = update_status(session, content_id=content.id, new_status=ContentStatus.REVISION_REQUESTED, review_comment=comment)
    assert updated.status == ContentStatus.REVISION_REQUESTED
    assert updated.review_comment == comment

    # Revision -> Approved (clears comment)
    updated = update_status(session, content_id=content.id, new_status=ContentStatus.APPROVED)
    assert updated.status == ContentStatus.APPROVED
    assert updated.review_comment is None

    # Approved -> Scheduled
    updated = update_status(session, content_id=content.id, new_status=ContentStatus.SCHEDULED)
    assert updated.status == ContentStatus.SCHEDULED

    # Scheduled -> Published (sets published_at)
    updated = update_status(session, content_id=content.id, new_status=ContentStatus.PUBLISHED)
    assert updated.status == ContentStatus.PUBLISHED
    assert updated.published_at is not None


def test_mark_as_posted(session: Session):
    """
    Test marking content as posted.
    """
    client = create_test_client(session)
    content = create(session, obj_in=ContentPieceCreate(client_id=client.id, title="Mark Posted Test", idea="i", angle="a", content_body="b"))

    # Cannot mark draft as posted
    with pytest.raises(HTTPException) as excinfo:
        mark_as_posted(session, content_id=content.id)
    assert excinfo.value.status_code == 400

    # Approve first
    update_status(session, content_id=content.id, new_status=ContentStatus.APPROVED)

    # Mark as posted
    marked = mark_as_posted(session, content_id=content.id)
    assert marked.published_at is not None
    first_published_at = marked.published_at

    # Mark again (should be idempotent)
    marked_again = mark_as_posted(session, content_id=content.id)
    assert marked_again.published_at == first_published_at # Timestamp shouldn't change


def test_rate_content(session: Session):
    """
    Test rating a content piece.
    """
    client = create_test_client(session, email="rate.client@test.com")
    # Ensure user is attached to the profile returned by the helper
    assert client.user is not None, "User not attached to client profile in helper"
    client_user = client.user # Get the user associated with the client profile

    content = create(session, obj_in=ContentPieceCreate(client_id=client.id, title="Rate Test", idea="i", angle="a", content_body="b"))

    # Cannot rate if not approved/published
    rating_in = ContentRatingInput(rating=4.5)
    with pytest.raises(HTTPException) as excinfo:
        rate_content(session, content_id=content.id, rating_in=rating_in, client_user=client_user)
    assert excinfo.value.status_code == 400
    assert "approved or published" in excinfo.value.detail.lower()

    # Approve the content
    update_status(session, content_id=content.id, new_status=ContentStatus.APPROVED)

    # Rate the content (valid rating)
    rated_content = rate_content(session, content_id=content.id, rating_in=rating_in, client_user=client_user)
    assert rated_content.client_rating == 4.5

    # Try creating invalid rating input (wrong step) - should raise ValidationError
    with pytest.raises(ValidationError) as excinfo_step:
        invalid_rating_in_step = ContentRatingInput(rating=4.2)
    # Check specific Pydantic v2 error message
    assert "Rating must be in 0.5 increments" in str(excinfo_step.value)

    # Try creating invalid rating input (too high) - should raise ValidationError
    with pytest.raises(ValidationError) as excinfo_high:
        invalid_rating_in_high = ContentRatingInput(rating=6.0)
    # Check specific Pydantic v2 error message
    assert "Input should be less than or equal to 5" in str(excinfo_high.value)

    # Try creating invalid rating input (too low) - should raise ValidationError
    with pytest.raises(ValidationError) as excinfo_low:
        invalid_rating_in_low = ContentRatingInput(rating=-1.0)
    # Check specific Pydantic v2 error message
    assert "Input should be greater than or equal to 0" in str(excinfo_low.value)

    # Try rating content belonging to another client
    other_client = create_test_client(session, email="other.rate.client@test.com", company="Other Rate Co")
    assert other_client.user is not None, "User not attached to other client profile in helper"
    other_client_user = other_client.user
    with pytest.raises(HTTPException) as excinfo_perm:
        rate_content(session, content_id=content.id, rating_in=rating_in, client_user=other_client_user)
    assert excinfo_perm.value.status_code == 403 # Forbidden

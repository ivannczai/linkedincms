"""
Content endpoints module.

This module contains endpoints for content piece management.
"""
from typing import Any, List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlmodel import Session

# Import crud functions directly for clarity
from app.crud import content as crud_content, client as crud_client, user as crud_user, scheduled_post as crud_scheduled_post
from app.api.deps import get_current_admin_user, get_current_user, get_current_client_user, get_session
from app.models.content import (
    ContentPiece,
    ContentPieceCreate,
    ContentPieceRead,
    ContentPieceUpdate,
    ContentStatus,
)
from app.crud.content import ContentRatingInput
from app.models.user import User, UserRole
from app.models.scheduled_post import ScheduledLinkedInPostCreate, PostStatus

router = APIRouter()


@router.get("/", response_model=List[ContentPieceRead])
def read_contents(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    client_id: Optional[int] = Query(None),
    status: Optional[ContentStatus] = Query(None),
    sort_by: Optional[str] = Query(None, description="Field to sort by (e.g., 'created_at', 'due_date')"), # Add sort_by
    sort_order: str = Query("desc", description="Sort order ('asc' or 'desc')"), # Add sort_order
    # active_only: bool = True, # Assuming is_active filtering is handled if needed
) -> Any:
    """
    Retrieve content pieces, with optional filtering and sorting.
    """
    # Validate sort_by field if provided (optional but good practice)
    allowed_sort_fields = ['created_at', 'updated_at', 'due_date', 'title', 'status']
    if sort_by and sort_by not in allowed_sort_fields:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid sort field. Allowed fields: {', '.join(allowed_sort_fields)}")

    # Validate sort_order
    if sort_order.lower() not in ["asc", "desc"]:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid sort order. Use 'asc' or 'desc'.")

    # Client permission check
    requesting_client_id = client_id
    if current_user.role == UserRole.CLIENT:
        # Use the correct CRUD function name for fetching client profile by user ID
        client_profile = crud_client.get_by_user_id(session, user_id=current_user.id) 
        if not client_profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client profile not found.")
        # If client is requesting, force filter by their ID and ignore passed client_id if different
        if requesting_client_id is not None and requesting_client_id != client_profile.id:
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Clients can only access their own content.")
        requesting_client_id = client_profile.id # Force client's own ID

    # Fetch contents using the updated CRUD function
    contents = crud_content.get_multi(
        session,
        skip=skip,
        limit=limit,
        client_id=requesting_client_id, # Use potentially overridden client_id
        status=status,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return contents


@router.post("/", response_model=ContentPieceRead)
def create_content(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
    content_in: ContentPieceCreate,
) -> Any:
    """
    Create a new content piece. (Admin only)
    """
    # Use the correct CRUD function name
    client = crud_client.get(session, content_in.client_id) 
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Client with ID {content_in.client_id} not found")

    # Use the correct CRUD function name
    content = crud_content.create(session=session, obj_in=content_in) 
    return content


@router.get("/{content_id}", response_model=ContentPieceRead)
def read_content(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    content_id: int,
) -> Any:
    """
    Get a specific content piece by ID.
    """
    # Use the correct CRUD function name
    content = crud_content.get(session, content_id) 
    if not content:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content piece not found")

    if current_user.role == UserRole.CLIENT:
        # Use the correct CRUD function name
        client_profile = crud_client.get_by_user_id(session, user_id=current_user.id) 
        if not client_profile or content.client_id != client_profile.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    return content


@router.put("/{content_id}", response_model=ContentPieceRead)
def update_content(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
    content_id: int,
    content_in: ContentPieceUpdate,
) -> Any:
    """
    Update a content piece. (Admin only)
    """
    content = crud_content.get(session, content_id) 
    if not content:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content piece not found")

    content = crud_content.update(session=session, db_obj=content, obj_in=content_in) 
    return content


@router.put("/client/{content_id}", response_model=ContentPieceRead)
def update_content_client(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_client_user),
    content_id: int,
    content_in: ContentPieceUpdate,
) -> Any:
    """
    Update a content piece. (Client only)
    """
    import traceback
    try:
        content = crud_content.get(session, content_id)
        if not content:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content piece not found")
        
        if content.client_id != current_user.client_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only edit your own content")
        
        if content.status == ContentStatus.PUBLISHED:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot edit published content")

        content = crud_content.update(session=session, db_obj=content, obj_in=content_in)
        return content
    except Exception as e:
        print('--- update_content_client error ---')
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/{content_id}", response_model=ContentPieceRead)
def delete_content(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
    content_id: int,
) -> Any:
    """
    Delete a content piece. (Admin only)
    """
    # Use the correct CRUD function name
    content = crud_content.get(session, content_id) 
    if not content:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content piece not found")

    # Use the correct CRUD function name
    deleted_content = crud_content.delete(session=session, content_id=content_id) 
    if not deleted_content:
         # This case might not be reachable if get succeeded, but keep for safety
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content piece found but failed to delete.") 
    return deleted_content


@router.post("/{content_id}/approve", response_model=ContentPieceRead)
def approve_content(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user), # Client action
    content_id: int,
) -> Any:
    """
    Approve a content piece. (Client only)
    """
    if current_user.role != UserRole.CLIENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only client users can approve content")

    # Use the correct CRUD function name
    content = crud_content.get(session, content_id) 
    if not content:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content piece not found")

    # Use the correct CRUD function name
    client_profile = crud_client.get_by_user_id(session, user_id=current_user.id) 
    if not client_profile or content.client_id != client_profile.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    if content.status != ContentStatus.PENDING_APPROVAL:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Content piece is not in {ContentStatus.PENDING_APPROVAL} status")

    # Use the correct CRUD function name
    content = crud_content.update_status(session=session, content_id=content_id, new_status=ContentStatus.APPROVED) 
    return content


@router.post("/{content_id}/request-revision", response_model=ContentPieceRead)
def request_revision(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user), # Client action
    content_id: int,
    review_comment: str = Body(..., embed=True, min_length=1),
) -> Any:
    """
    Request revision for a content piece. (Client only)
    """
    if current_user.role != UserRole.CLIENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only client users can request revision")

    # Use the correct CRUD function name
    content = crud_content.get(session, content_id) 
    if not content:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content piece not found")

    # Use the correct CRUD function name
    client_profile = crud_client.get_by_user_id(session, user_id=current_user.id) 
    if not client_profile or content.client_id != client_profile.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    if content.status != ContentStatus.PENDING_APPROVAL:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Content piece is not in {ContentStatus.PENDING_APPROVAL} status")

    # Use the correct CRUD function name
    content = crud_content.update_status(
        session=session,
        content_id=content_id,
        new_status=ContentStatus.REVISION_REQUESTED,
        review_comment=review_comment,
    )
    return content


@router.post("/{content_id}/submit", response_model=ContentPieceRead)
def submit_for_approval(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
    content_id: int,
) -> Any:
    """
    Submit a content piece for client approval. (Admin only)
    """
    # Use the correct CRUD function name
    content = crud_content.get(session, content_id) 
    if not content:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content piece not found")

    if content.status not in [ContentStatus.DRAFT, ContentStatus.REVISION_REQUESTED]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Content piece must be in {ContentStatus.DRAFT} or {ContentStatus.REVISION_REQUESTED} status")

    # Use the correct CRUD function name
    content = crud_content.update_status(session=session, content_id=content_id, new_status=ContentStatus.PENDING_APPROVAL)
    return content


@router.post("/{content_id}/mark-as-posted", response_model=ContentPieceRead)
def mark_content_as_posted(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user), # Client action
    content_id: int,
) -> Any:
    """
    Mark a content piece as posted by the client. (Client only)
    """
    if current_user.role != UserRole.CLIENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only client users can mark content as posted")

    # Use the correct CRUD function name
    content = crud_content.get(session, content_id) 
    if not content:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content piece not found")

    # Use the correct CRUD function name
    client_profile = crud_client.get_by_user_id(session, user_id=current_user.id) 
    if not client_profile or content.client_id != client_profile.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    # Use the correct CRUD function name (mark_as_posted handles status check)
    content = crud_content.mark_as_posted(session=session, content_id=content_id) 
    return content


@router.post("/{content_id}/publish", response_model=ContentPieceRead)
def publish_content( # Admin action to force publish
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
    content_id: int,
) -> Any:
    """
    Publish an approved content piece. (Admin only)
    """
    # Use the correct CRUD function name
    content = crud_content.get(session, content_id) 
    if not content:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content piece not found")

    # Use the correct CRUD function name (mark_as_posted handles status check)
    content = crud_content.mark_as_posted(session=session, content_id=content_id)
    return content

# --- New Rating Endpoint ---
@router.post("/{content_id}/rate", response_model=ContentPieceRead)
def rate_content_endpoint(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user), # Client action
    content_id: int,
    rating_in: ContentRatingInput = Body(...),
) -> Any:
    """
    Allows a client user to rate an approved or published content piece.
    """
    if current_user.role != UserRole.CLIENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only client users can rate content")

    # CRUD function handles checking ownership and status
    try:
        # Pass the authenticated user directly to the CRUD function
        # Use the correct CRUD function name
        content = crud_content.rate_content( 
            session=session,
            content_id=content_id,
            rating_in=rating_in,
            client_user=current_user
        )
        return content
    except HTTPException as e:
        raise e
    except ValueError as e:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        print(f"Unexpected error rating content: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.post("/{content_id}/schedule", response_model=ContentPieceRead)
def schedule_content(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user), # Client action
    content_id: int,
    scheduled_at: str = Body(..., embed=True),
) -> Any:
    """
    Schedule a content piece for publication. (Client only)
    """
    if current_user.role != UserRole.CLIENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only client users can schedule content")

    content = crud_content.get(session, content_id)
    if not content:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content piece not found")

    client_profile = crud_client.get_by_user_id(session, user_id=current_user.id)
    if not client_profile or content.client_id != client_profile.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    if content.status != ContentStatus.APPROVED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Content must be approved to be scheduled")

    # Convert scheduled_at string to datetime
    try:
        # Parse the input datetime string and convert to UTC
        scheduled_at_dt = datetime.fromisoformat(scheduled_at)
        if scheduled_at_dt.tzinfo is None:
            scheduled_at_dt = scheduled_at_dt.replace(tzinfo=timezone.utc)
            
        print(f"\nЗаплановано на (UTC): {scheduled_at_dt.isoformat()}")
        print(f"Заплановано на (локальний): {scheduled_at_dt.astimezone().isoformat()}")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SSZ)")

    # Check if date is in the future
    now = datetime.now(timezone.utc)
    print(f"Поточний час (UTC): {now.isoformat()}")
    print(f"Поточний час (локальний): {now.astimezone().isoformat()}")
    
    if scheduled_at_dt <= now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Scheduled time must be in the future")

    # Create scheduled post record first
    scheduled_post = crud_scheduled_post.create_scheduled_post(
        session=session,
        obj_in=ScheduledLinkedInPostCreate(
            user_id=current_user.id,
            content_id=content.id,
            content_text=content.content_body,
            scheduled_at=scheduled_at_dt,
            status=PostStatus.PENDING
        )
    )
    print(f"\nСтворено запланований пост ID: {scheduled_post.id}")
    print(f"Статус: {scheduled_post.status}")
    print(f"Заплановано на (UTC): {scheduled_post.scheduled_at.isoformat()}")
    print(f"Заплановано на (локальний): {scheduled_post.scheduled_at.astimezone().isoformat()}")

    # Update content status after successful post creation
    content = crud_content.update(
        session=session,
        db_obj=content,
        obj_in=ContentPieceUpdate(
            status=ContentStatus.SCHEDULED,
            scheduled_at=scheduled_at_dt
        )
    )
    print(f"\nОновлено статус контенту ID: {content.id}")
    print(f"Статус: {content.status}")
    print(f"Заплановано на (UTC): {content.scheduled_at.isoformat() if content.scheduled_at else 'None'}")
    print(f"Заплановано на (локальний): {content.scheduled_at.astimezone().isoformat() if content.scheduled_at else 'None'}")

    return content

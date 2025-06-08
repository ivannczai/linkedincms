"""
Content endpoints module.

This module contains endpoints for content piece management.
"""
from typing import Any, List, Optional
from datetime import datetime, timezone, timedelta
import os
import requests
import logging

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, Form, File, UploadFile
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
from app.core.security import decrypt_data

router = APIRouter()
logger = logging.getLogger(__name__)


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
async def create_content(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
    title: str = Form(...),
    idea: str = Form(...),
    angle: str = Form(...),
    content_body: str = Form(...),
    client_id: int = Form(...),
    is_active: bool = Form(True),
    attachments: List[UploadFile] = File(None),
):
    """Create new content piece."""
    import traceback
    try:
        client = crud_client.get(session=session, client_id=client_id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )

        content_in = ContentPieceCreate(
            title=title,
            idea=idea,
            angle=angle,
            content_body=content_body,
            client_id=client_id,
            is_active=is_active
        )

        content = await crud_content.content.create(
            session=session,
            obj_in=content_in,
            attachments=attachments
        )
        return content
    except Exception as e:
        print('--- create_content error ---')
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


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
async def update_content(
    *,
    content_id: int,
    title: str = Form(None),
    idea: str = Form(None),
    angle: str = Form(None),
    content_body: str = Form(None),
    is_active: bool = Form(None),
    status: ContentStatus = Form(None),
    attachments: List[UploadFile] = File(None),
    existing_attachments: List[str] = Form(None),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Update content piece."""
    print(f"Update content request - ID: {content_id}")
    print(f"Title: {title}")
    print(f"Idea: {idea}")
    print(f"Angle: {angle}")
    print(f"Content body length: {len(content_body) if content_body else 0}")
    print(f"Is active: {is_active}")
    print(f"Status: {status}")
    print(f"Attachments count: {len(attachments) if attachments else 0}")
    print(f"Existing attachments: {existing_attachments}")
    
    content = crud_content.get(db, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content piece not found")
    
    # Створюємо словник з даними для оновлення
    update_data = {}
    if title is not None:
        update_data["title"] = title
    if idea is not None:
        update_data["idea"] = idea
    if angle is not None:
        update_data["angle"] = angle
    if content_body is not None:
        update_data["content_body"] = content_body
    if is_active is not None:
        update_data["is_active"] = is_active
    if status is not None:
        if current_user.role == UserRole.ADMIN:
            update_data["status"] = status
        else:
            raise HTTPException(status_code=403, detail="Only admin can change content status")
    
    print(f"Update data: {update_data}")
    
    # Створюємо об'єкт ContentPieceUpdate
    content_update = ContentPieceUpdate(**update_data)
    
    # Оновлюємо контент
    content = await crud_content.content.update(
        db=db,
        db_obj=content,
        obj_in=content_update,
        user=current_user,
        attachments=attachments,
        existing_attachments=existing_attachments
    )
    return content


@router.put("/client/{content_id}", response_model=ContentPieceRead)
async def update_content_client(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_client_user),
    content_id: int,
    title: str = Form(...),
    idea: str = Form(...),
    angle: str = Form(...),
    content_body: str = Form(...),
    is_active: bool = Form(True),
    status: ContentStatus = Form(...),
    attachments: List[UploadFile] = File(None),
    existing_attachments: List[str] = Form(None),
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

        content_in = ContentPieceUpdate(
            title=title,
            idea=idea,
            angle=angle,
            content_body=content_body,
            is_active=is_active,
            status=status
        )

        content = await crud_content.content.update(
            db=session,
            db_obj=content,
            obj_in=content_in,
            user=current_user,
            attachments=attachments,
            existing_attachments=existing_attachments
        )
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

@router.post("/{content_id}/post-now", response_model=ContentPieceRead)
async def post_content_now(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    content_id: int,
) -> Any:
    """
    Post content immediately.
    """
    # Get content
    content = crud_content.get(session=session, content_id=content_id)
    if not content:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")
    
    # Get client profile
    client_profile = crud_client.get_by_user_id(session=session, user_id=current_user.id)
    if not client_profile:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client profile not found")
    
    # Check permissions
    if content.client_id != client_profile.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    
    # Check content status
    if content.status not in [ContentStatus.DRAFT, ContentStatus.REVISION_REQUESTED, ContentStatus.APPROVED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot post content with status {content.status}"
        )

    # Handle media assets if content has attachments
    media_assets = []
    if content.attachments:
        try:
            # Get LinkedIn access token
            if not current_user.linkedin_access_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="LinkedIn account not connected"
                )
            
            access_token = decrypt_data(current_user.linkedin_access_token)
            
            # Upload each attachment to LinkedIn
            for attachment in content.attachments:
                try:
                    # Register upload
                    register_url = "https://api.linkedin.com/v2/assets?action=registerUpload"
                    register_headers = {
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                        "X-Restli-Protocol-Version": "2.0.0"
                    }
                    register_data = {
                        "registerUploadRequest": {
                            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                            "owner": f"urn:li:person:{current_user.linkedin_id}",
                            "serviceRelationships": [
                                {
                                    "relationshipType": "OWNER",
                                    "identifier": "urn:li:userGeneratedContent"
                                }
                            ]
                        }
                    }
                    
                    logger.info(f"Registering upload for {attachment}")
                    register_response = requests.post(register_url, headers=register_headers, json=register_data)
                    register_response.raise_for_status()
                    upload_data = register_response.json()
                    logger.info(f"Upload registration response: {upload_data}")
                    
                    # Upload file
                    upload_url = upload_data["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
                    asset = upload_data["value"]["asset"]
                    
                    # Read file from uploads directory
                    file_path = attachment if os.path.exists(attachment) else os.path.join("uploads", attachment)
                    if not os.path.exists(file_path):
                        logger.error(f"File not found: {file_path}")
                        continue
                        
                    logger.info(f"Uploading file {file_path} to LinkedIn")
                    with open(file_path, "rb") as f:
                        upload_response = requests.put(upload_url, data=f.read(), headers={"Authorization": f"Bearer {access_token}"})
                        upload_response.raise_for_status()
                    logger.info(f"File uploaded successfully, asset: {asset}")
                    
                    # Add asset URN to list
                    media_assets.append({
                        "status": "READY",
                        "media": asset
                    })
                    logger.info(f"Added media asset to list: {media_assets[-1]}")
                    
                except Exception as e:
                    logger.error(f"Failed to upload {attachment} to LinkedIn: {str(e)}")
                    if hasattr(e, 'response'):
                        logger.error(f"Response content: {e.response.content}")
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to process media assets: {str(e)}")
            # Continue without media assets if there's an error

    # Create scheduled post record with 5 second delay
    logger.info(f"Creating immediate post with content: {content.content_body}")
    logger.info(f"Creating immediate post with media assets: {media_assets}")
    scheduled_post = crud_scheduled_post.create_scheduled_post(
        session=session,
        obj_in=ScheduledLinkedInPostCreate(
            user_id=current_user.id,
            content_id=content.id,
            content_text=content.content_body,
            scheduled_at=datetime.now(timezone.utc) + timedelta(seconds=5),
            status=PostStatus.PENDING,
            media_assets=media_assets if media_assets else None
        )
    )
    logger.info(f"Created immediate post: {scheduled_post}")

    # Mark content as posted immediately
    content = crud_content.update_status(
        session=session,
        content_id=content.id,
        new_status=ContentStatus.PUBLISHED,
        scheduled_at=datetime.now(timezone.utc) + timedelta(seconds=5)
    )

    return content

@router.post("/{content_id}/schedule", response_model=ContentPieceRead)
async def schedule_content(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    content_id: int,
    scheduled_at: str = Body(..., embed=True),
) -> Any:
    """
    Schedule content for publishing.
    """
    # Get content
    content = crud_content.get(session=session, content_id=content_id)
    if not content:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")
    
    # Get client profile
    client_profile = crud_client.get_by_user_id(session=session, user_id=current_user.id)
    if not client_profile:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client profile not found")
    
    # Check permissions
    if content.client_id != client_profile.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    
    # Check content status
    if content.status not in [ContentStatus.DRAFT, ContentStatus.REVISION_REQUESTED, ContentStatus.APPROVED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot schedule content with status {content.status}"
        )
    
    # Parse scheduled time
    try:
        scheduled_at_dt = datetime.fromisoformat(scheduled_at)
        if scheduled_at_dt.tzinfo is None:
            scheduled_at_dt = scheduled_at_dt.replace(tzinfo=timezone.utc)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date format")
    
    # Check if scheduled time is in the future
    now = datetime.now(timezone.utc)
    if scheduled_at_dt <= now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Scheduled time must be in the future")

    # Handle media assets if content has attachments
    media_assets = []
    if content.attachments:
        try:
            # Get LinkedIn access token
            if not current_user.linkedin_access_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="LinkedIn account not connected"
                )
            
            access_token = decrypt_data(current_user.linkedin_access_token)
            
            # Upload each attachment to LinkedIn
            for attachment in content.attachments:
                try:
                    # Register upload
                    register_url = "https://api.linkedin.com/v2/assets?action=registerUpload"
                    register_headers = {
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                        "X-Restli-Protocol-Version": "2.0.0"
                    }
                    register_data = {
                        "registerUploadRequest": {
                            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                            "owner": f"urn:li:person:{current_user.linkedin_id}",
                            "serviceRelationships": [
                                {
                                    "relationshipType": "OWNER",
                                    "identifier": "urn:li:userGeneratedContent"
                                }
                            ]
                        }
                    }
                    
                    logger.info(f"Registering upload for {attachment}")
                    register_response = requests.post(register_url, headers=register_headers, json=register_data)
                    register_response.raise_for_status()
                    upload_data = register_response.json()
                    logger.info(f"Upload registration response: {upload_data}")
                    
                    # Upload file
                    upload_url = upload_data["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
                    asset = upload_data["value"]["asset"]
                    
                    # Read file from uploads directory
                    file_path = attachment if os.path.exists(attachment) else os.path.join("uploads", attachment)
                    if not os.path.exists(file_path):
                        logger.error(f"File not found: {file_path}")
                        continue
                        
                    logger.info(f"Uploading file {file_path} to LinkedIn")
                    with open(file_path, "rb") as f:
                        upload_response = requests.put(upload_url, data=f.read(), headers={"Authorization": f"Bearer {access_token}"})
                        upload_response.raise_for_status()
                    logger.info(f"File uploaded successfully, asset: {asset}")
                    
                    # Add asset URN to list
                    media_assets.append({
                        "status": "READY",
                        "media": asset
                    })
                    logger.info(f"Added media asset to list: {media_assets[-1]}")
                    
                except Exception as e:
                    logger.error(f"Failed to upload {attachment} to LinkedIn: {str(e)}")
                    if hasattr(e, 'response'):
                        logger.error(f"Response content: {e.response.content}")
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to process media assets: {str(e)}")
            # Continue without media assets if there's an error

    # Create scheduled post record with 5 second delay
    logger.info(f"Creating scheduled post with content: {content.content_body}")
    logger.info(f"Creating scheduled post with media assets: {media_assets}")
    scheduled_post = crud_scheduled_post.create_scheduled_post(
        session=session,
        obj_in=ScheduledLinkedInPostCreate(
            user_id=current_user.id,
            content_id=content.id,
            content_text=content.content_body,
            scheduled_at=scheduled_at_dt,
            status=PostStatus.PENDING,
            media_assets=media_assets if media_assets else None
        )
    )
    logger.info(f"Created scheduled post: {scheduled_post}")

    # Update content status to scheduled
    content = crud_content.update_status(
        session=session, 
        content_id=content.id, 
        new_status=ContentStatus.SCHEDULED,
        scheduled_at=scheduled_at_dt
    )
    
    # Update scheduled_at field
    content.scheduled_at = scheduled_at_dt
    session.add(content)
    session.commit()
    session.refresh(content)

    return content

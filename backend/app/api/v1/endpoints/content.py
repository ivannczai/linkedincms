"""
Content endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import crud_content
from app.schemas.content import ContentPiece, ContentPieceCreate, ContentPieceUpdate
from app.models.user import User

router = APIRouter()

@router.put("/{content_id}", response_model=ContentPiece)
def update_content(
    *,
    db: Session = Depends(deps.get_db),
    content_id: int,
    content_in: ContentPieceUpdate,
    current_user: User = Depends(deps.get_current_user)
) -> ContentPiece:
    """Update content piece."""
    content = crud_content.content.get(db, id=content_id)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    return crud_content.content.update(
        db=db,
        db_obj=content,
        obj_in=content_in,
        user=current_user
    ) 
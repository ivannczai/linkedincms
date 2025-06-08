"""
LinkedIn service module.

This module contains functions for interacting with LinkedIn API.
"""
import logging
import requests
from typing import Optional
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.security import decrypt_data
from app.models.user import User

logger = logging.getLogger(__name__)

def get_access_token(user: User) -> str:
    """Get LinkedIn access token for user."""
    if not user.linkedin_access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LinkedIn account not connected"
        )
    return decrypt_data(user.linkedin_access_token)

def register_upload(access_token: str, user_id: str) -> dict:
    """Register a file upload with LinkedIn."""
    url = "https://api.linkedin.com/v2/assets?action=registerUpload"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    
    data = {
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "owner": f"urn:li:person:{user_id}",
            "serviceRelationships": [
                {
                    "relationshipType": "OWNER",
                    "identifier": "urn:li:userGeneratedContent"
                }
            ]
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"LinkedIn API error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"LinkedIn API error: {str(e)}"
        )

def upload_file(upload_url: str, file_path: str, content_type: str) -> None:
    """Upload a file to LinkedIn."""
    try:
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        headers = {
            "Content-Type": content_type
        }
        
        response = requests.put(upload_url, headers=headers, data=file_content)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"LinkedIn API error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"LinkedIn API error: {str(e)}"
        )

def upload_to_linkedin(file_path: str, user: User) -> str:
    """Upload a file to LinkedIn and return the asset URN."""
    try:
        # Get access token
        access_token = get_access_token(user)
        
        # Register upload
        upload_info = register_upload(access_token, user.linkedin_id)
        upload_url = upload_info["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
        asset = upload_info["value"]["asset"]
        
        # Upload file
        upload_file(upload_url, file_path, "image/jpeg")  # or "image/png" based on file type
        
        return f"urn:li:digitalmediaAsset:{asset}"
    except Exception as e:
        logger.error(f"Failed to upload file to LinkedIn: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to upload file to LinkedIn: {str(e)}"
        ) 
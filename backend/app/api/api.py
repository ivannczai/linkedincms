"""
API router module.

This module contains the main API router that includes all endpoint routers.
"""
from fastapi import APIRouter

from app.api.endpoints import auth, users, clients, contents, linkedin # Import linkedin router

# Main API router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
api_router.include_router(contents.router, prefix="/contents", tags=["contents"])
api_router.include_router(linkedin.router, prefix="/linkedin", tags=["linkedin"]) # Include linkedin router

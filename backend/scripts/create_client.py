#!/usr/bin/env python
"""
Script to create a client user and associated client profile in the database.
Run this script after setting up the database and creating an admin user.
"""

import asyncio
import sys
import os

# Add the parent directory to the path so we can import from the app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.client import ClientProfile
from app.core.database import get_session
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession


def create_client_user(email: str, password: str, company_name: str, industry: str, contact_name: str):
    """Create a client user with the given details and an associated client profile."""
    session = next(get_session())
    try:
        # Check if user already exists
        result = session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if user:
            print(f"User with email {email} already exists.")
            return
        
        # Create new client user
        hashed_password = get_password_hash(password)
        client_user = User(
            email=email,
            hashed_password=hashed_password,
            role=UserRole.CLIENT,
            is_active=True,
            full_name=contact_name  # Adding required field
        )
        
        session.add(client_user)
        session.commit()
        session.refresh(client_user)
        
        # Create client profile
        client_profile = ClientProfile(
            company_name=company_name,
            industry=industry,
            contact_name=contact_name,
            user_id=client_user.id,
            is_active=True,
        )
        
        session.add(client_profile)
        session.commit()
        session.refresh(client_profile)
        
        print(f"Client user created successfully with ID: {client_user.id}")
        print(f"Client profile created successfully with ID: {client_profile.id}")
    finally:
        session.close()


def main():
    """Main function to create a client user and profile."""
    if len(sys.argv) != 6:
        print("Usage: python create_client.py <email> <password> <company_name> <industry> <contact_name>")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    company_name = sys.argv[3]
    industry = sys.argv[4]
    contact_name = sys.argv[5]
    
    create_client_user(email, password, company_name, industry, contact_name)


if __name__ == "__main__":
    main()

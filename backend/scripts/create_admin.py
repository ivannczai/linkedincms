#!/usr/bin/env python
"""
Script to create an admin user in the database.
Run this script after setting up the database to create the initial admin user.
"""

import asyncio
import sys
import os

# Add the parent directory to the path so we can import from the app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.core.database import get_session
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession


def create_admin_user(email: str, password: str):
    """Create an admin user with the given email and password."""
    session = next(get_session())
    try:
        # Check if user already exists
        result = session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if user:
            print(f"User with email {email} already exists.")
            return
        
        # Create new admin user
        hashed_password = get_password_hash(password)
        admin_user = User(
            email=email,
            hashed_password=hashed_password,
            role=UserRole.ADMIN,
            is_active=True,
            full_name="Admin User"  # Adding required field
        )
        
        session.add(admin_user)
        session.commit()
        session.refresh(admin_user)
        
        print(f"Admin user created successfully with ID: {admin_user.id}")
    finally:
        session.close()


def main():
    """Main function to create an admin user."""
    if len(sys.argv) != 3:
        print("Usage: python create_admin.py <email> <password>")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    
    create_admin_user(email, password)


if __name__ == "__main__":
    main()

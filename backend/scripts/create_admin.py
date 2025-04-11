#!/usr/bin/env python
"""
Script to create an admin user in the database.
Run this script after setting up the database to create the initial admin user.
"""

import asyncio
import sys
import os
from pathlib import Path # Import Path
from dotenv import load_dotenv # Import load_dotenv

# Add the parent directory to the path so we can import from the app
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# Instead, determine project root relative to this script
project_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_dir / "backend"))

# Explicitly load the .env file from the project root
env_path = project_dir / '.env'
if env_path.exists():
    print(f"Loading environment variables from: {env_path}")
    load_dotenv(dotenv_path=env_path, override=True) # Override existing env vars if needed
else:
    print(f"Warning: .env file not found at {env_path}")

# Now import app modules AFTER potentially loading .env
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.core.database import get_session
from sqlmodel import select
# from sqlmodel.ext.asyncio.session import AsyncSession # Not used


def create_admin_user(email: str, password: str):
    """Create an admin user with the given email and password."""
    print("Attempting to get database session...")
    session = next(get_session())
    print("Database session obtained.")
    try:
        # Check if user already exists
        print(f"Checking if user {email} exists...")
        result = session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user:
            print(f"User with email {email} already exists.")
            return

        # Create new admin user
        print(f"Creating user {email}...")
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
    except Exception as e:
        print(f"Error during admin user creation: {e}")
        # Optionally re-raise the exception if needed
        # raise
    finally:
        print("Closing database session.")
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

"""
Database connection module.

This module provides the database session and engine for the application.
"""
from sqlmodel import SQLModel, Session, create_engine
from typing import Generator

from app.core.config import settings

# Create SQLAlchemy engine
# Removed connect_args={"check_same_thread": False} as it's for SQLite only
engine = create_engine(
    str(settings.DATABASE_URL),
    echo=False,  # Set to True to see SQL queries in console
)


def create_db_and_tables() -> None:
    """
    Create database tables from SQLModel models.

    This function should be called during application startup.
    """
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """
    Get a database session.

    This function is used as a dependency in FastAPI endpoints.

    Yields:
        Generator[Session, None, None]: A SQLModel session
    """
    with Session(engine) as session:
        yield session

"""Database setup and session management."""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import NullPool
from authlib.config import Config

# Base class for all models
Base = declarative_base()


class Database:
    """Database connection and session management."""

    def __init__(self, database_url: str) -> None:
        """
        Initialize database connection.

        Args:
            database_url: Database connection URL
        """
        self.database_url = database_url
        self.engine = create_engine(
            database_url,
            poolclass=NullPool,  # Disable connection pooling for better control
            echo=False,
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )

    def create_all_tables(self) -> None:
        """Create all database tables from models."""
        Base.metadata.create_all(bind=self.engine)

    def drop_all_tables(self) -> None:
        """Drop all database tables (use with caution)."""
        Base.metadata.drop_all(bind=self.engine)

    def get_session(self) -> Generator[Session, None, None]:
        """
        Get a database session generator for dependency injection.

        Yields:
            SQLAlchemy Session
        """
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()

    def create_session(self) -> Session:
        """
        Create a new database session.

        Returns:
            SQLAlchemy Session
        """
        return self.SessionLocal()

    def close_connection(self) -> None:
        """Close database connection."""
        self.engine.dispose()


# Initialize database with config
_config = Config()
db = Database(database_url=_config.DATABASE_URL)

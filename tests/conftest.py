"""Pytest configuration and fixtures."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from authlib.database import Base
from authlib.config import TestConfig


@pytest.fixture(scope="function")
def test_db_engine():
    """Create a test database engine."""
    # Use in-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """Create a test database session."""
    TestSessionLocal = sessionmaker(bind=test_db_engine)
    session = TestSessionLocal()
    yield session
    session.close()


@pytest.fixture
def test_config():
    """Get test configuration."""
    return TestConfig()


@pytest.fixture
def test_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "first_name": "John",
        "last_name": "Doe",
    }


@pytest.fixture
def test_user_data_2():
    """Sample user data for testing (second user)."""
    return {
        "email": "test2@example.com",
        "password": "TestPassword456!",
        "first_name": "Jane",
        "last_name": "Smith",
    }

"""Tests for JWT utilities."""

import pytest
from datetime import datetime, timedelta, timezone
from authlib.utils.jwt_handler import JWTHandler
from authlib.utils.exceptions import InvalidToken
from authlib.config import TestConfig


class TestJWTHandler:
    """Test cases for JWTHandler."""

    @pytest.fixture
    def jwt_handler(self):
        """Create a JWT handler for testing."""
        return JWTHandler(config=TestConfig())

    def test_create_access_token(self, jwt_handler):
        """Test creating an access token."""
        user_id = 1
        email = "test@example.com"

        token = jwt_handler.create_access_token(user_id=user_id, email=email)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self, jwt_handler):
        """Test creating a refresh token."""
        user_id = 1
        email = "test@example.com"

        token = jwt_handler.create_refresh_token(user_id=user_id, email=email)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_access_token(self, jwt_handler):
        """Test verifying an access token."""
        user_id = 1
        email = "test@example.com"

        token = jwt_handler.create_access_token(user_id=user_id, email=email)
        payload = jwt_handler.verify_access_token(token)

        assert payload["user_id"] == user_id
        assert payload["email"] == email
        assert payload["token_type"] == "access"

    def test_verify_refresh_token(self, jwt_handler):
        """Test verifying a refresh token."""
        user_id = 1
        email = "test@example.com"

        token = jwt_handler.create_refresh_token(user_id=user_id, email=email)
        payload = jwt_handler.verify_refresh_token(token)

        assert payload["user_id"] == user_id
        assert payload["email"] == email
        assert payload["token_type"] == "refresh"

    def test_verify_invalid_token(self, jwt_handler):
        """Test verifying an invalid token."""
        with pytest.raises(InvalidToken):
            jwt_handler.verify_token("invalid_token")

    def test_verify_expired_token(self, jwt_handler):
        """Test verifying an expired token."""
        user_id = 1
        email = "test@example.com"

        # Create handler with very short expiry
        config = TestConfig()
        config.JWT_ACCESS_TOKEN_EXPIRY_MINUTES = 0  # Expires immediately
        handler = JWTHandler(config=config)

        token = handler.create_access_token(user_id=user_id, email=email)

        # Sleep to ensure expiry
        import time
        time.sleep(1)

        with pytest.raises(InvalidToken):
            handler.verify_access_token(token)

    def test_create_password_reset_token(self, jwt_handler):
        """Test creating a password reset token."""
        user_id = 1
        email = "test@example.com"

        token = jwt_handler.create_password_reset_token(
            user_id=user_id,
            email=email,
        )

        assert isinstance(token, str)

    def test_verify_password_reset_token(self, jwt_handler):
        """Test verifying a password reset token."""
        user_id = 1
        email = "test@example.com"

        token = jwt_handler.create_password_reset_token(
            user_id=user_id,
            email=email,
        )
        payload = jwt_handler.verify_password_reset_token(token)

        assert payload["user_id"] == user_id
        assert payload["email"] == email
        assert payload["token_type"] == "password_reset"

    def test_get_user_id_from_token(self, jwt_handler):
        """Test extracting user ID from token."""
        user_id = 1
        email = "test@example.com"

        token = jwt_handler.create_access_token(user_id=user_id, email=email)
        extracted_id = jwt_handler.get_user_id_from_token(token)

        assert extracted_id == user_id

    def test_is_token_expired(self, jwt_handler):
        """Test checking if token is expired."""
        user_id = 1
        email = "test@example.com"

        token = jwt_handler.create_access_token(user_id=user_id, email=email)
        assert not jwt_handler.is_token_expired(token)

    def test_additional_claims(self, jwt_handler):
        """Test adding additional claims to token."""
        user_id = 1
        email = "test@example.com"
        additional_claims = {"role": "admin", "permissions": ["read", "write"]}

        token = jwt_handler.create_access_token(
            user_id=user_id,
            email=email,
            additional_claims=additional_claims,
        )
        payload = jwt_handler.verify_access_token(token)

        assert payload["role"] == "admin"
        assert payload["permissions"] == ["read", "write"]

    def test_create_token_invalid_user_id(self, jwt_handler):
        """Test creating token with invalid user ID."""
        with pytest.raises(ValueError):
            jwt_handler.create_access_token(user_id=None, email="test@example.com")

    def test_create_token_invalid_email(self, jwt_handler):
        """Test creating token with invalid email."""
        with pytest.raises(ValueError):
            jwt_handler.create_access_token(user_id=1, email=None)

    def test_verify_wrong_token_type(self, jwt_handler):
        """Test verifying token with wrong type."""
        user_id = 1
        email = "test@example.com"

        # Create refresh token but try to verify as access token
        refresh_token = jwt_handler.create_refresh_token(
            user_id=user_id,
            email=email,
        )

        with pytest.raises(InvalidToken):
            jwt_handler.verify_access_token(refresh_token)

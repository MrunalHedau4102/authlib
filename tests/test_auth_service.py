"""Tests for authentication service."""

import pytest
from authlib.services.auth_service import AuthService
from authlib.utils.exceptions import (
    UserNotFound,
    InvalidCredentials,
    InvalidToken,
    UserAlreadyExists,
    ValidationError,
)


class TestAuthService:
    """Test cases for AuthService."""

    def test_register_user(self, test_db_session, test_user_data):
        """Test user registration."""
        auth_service = AuthService(test_db_session)

        result = auth_service.register(
            email=test_user_data["email"],
            password=test_user_data["password"],
            first_name=test_user_data["first_name"],
            last_name=test_user_data["last_name"],
        )

        assert "user" in result
        assert "access_token" in result
        assert "refresh_token" in result
        assert result["user"]["email"] == test_user_data["email"]
        assert result["token_type"] == "Bearer"

    def test_register_duplicate_user(self, test_db_session, test_user_data):
        """Test registering a duplicate user."""
        auth_service = AuthService(test_db_session)

        # Register first user
        auth_service.register(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )

        # Try to register duplicate
        with pytest.raises(UserAlreadyExists):
            auth_service.register(
                email=test_user_data["email"],
                password=test_user_data["password"],
            )

    def test_register_invalid_email(self, test_db_session):
        """Test registration with invalid email."""
        auth_service = AuthService(test_db_session)

        with pytest.raises(ValidationError):
            auth_service.register(
                email="invalid-email",
                password="ValidPass123!",
            )

    def test_register_weak_password(self, test_db_session):
        """Test registration with weak password."""
        auth_service = AuthService(test_db_session)

        with pytest.raises(ValidationError):
            auth_service.register(
                email="test@example.com",
                password="weak",
            )

    def test_login_success(self, test_db_session, test_user_data):
        """Test successful login."""
        auth_service = AuthService(test_db_session)

        # Register user first
        auth_service.register(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )

        # Login
        result = auth_service.login(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )

        assert "user" in result
        assert "access_token" in result
        assert "refresh_token" in result
        assert result["user"]["email"] == test_user_data["email"]

    def test_login_user_not_found(self, test_db_session):
        """Test login with non-existent user."""
        auth_service = AuthService(test_db_session)

        with pytest.raises(UserNotFound):
            auth_service.login(
                email="nonexistent@example.com",
                password="SomePass123!",
            )

    def test_login_wrong_password(self, test_db_session, test_user_data):
        """Test login with wrong password."""
        auth_service = AuthService(test_db_session)

        # Register user
        auth_service.register(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )

        # Try to login with wrong password
        with pytest.raises(InvalidCredentials):
            auth_service.login(
                email=test_user_data["email"],
                password="WrongPassword456!",
            )

    def test_refresh_access_token(self, test_db_session, test_user_data):
        """Test refreshing access token."""
        auth_service = AuthService(test_db_session)

        # Register and login
        login_result = auth_service.register(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )
        refresh_token = login_result["refresh_token"]

        # Refresh token
        result = auth_service.refresh_access_token(refresh_token)

        assert "access_token" in result
        assert result["token_type"] == "Bearer"

    def test_refresh_token_invalid(self, test_db_session):
        """Test refreshing with invalid token."""
        auth_service = AuthService(test_db_session)

        with pytest.raises(InvalidToken):
            auth_service.refresh_access_token("invalid_token")

    def test_logout(self, test_db_session, test_user_data):
        """Test user logout."""
        auth_service = AuthService(test_db_session)

        # Register and login
        login_result = auth_service.register(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )
        access_token = login_result["access_token"]

        # Logout
        auth_service.logout(access_token, token_type="access")

        # Try to verify token (should fail as it's blacklisted)
        with pytest.raises(InvalidToken):
            auth_service.verify_token(access_token)

    def test_request_password_reset(self, test_db_session, test_user_data):
        """Test password reset request."""
        auth_service = AuthService(test_db_session)

        # Register user
        auth_service.register(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )

        # Request password reset
        result = auth_service.request_password_reset(test_user_data["email"])

        assert "reset_token" in result
        assert result["token_type"] == "Bearer"

    def test_request_password_reset_user_not_found(self, test_db_session):
        """Test password reset request for non-existent user."""
        auth_service = AuthService(test_db_session)

        with pytest.raises(UserNotFound):
            auth_service.request_password_reset("nonexistent@example.com")

    def test_confirm_password_reset(self, test_db_session, test_user_data):
        """Test confirming password reset."""
        auth_service = AuthService(test_db_session)

        # Register user
        auth_service.register(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )

        # Request password reset
        reset_result = auth_service.request_password_reset(test_user_data["email"])
        reset_token = reset_result["reset_token"]

        # Confirm password reset
        new_password = "NewPassword789!"
        result = auth_service.confirm_password_reset(reset_token, new_password)

        assert "user" in result
        assert "access_token" in result

        # Verify can login with new password
        login_result = auth_service.login(
            email=test_user_data["email"],
            password=new_password,
        )
        assert login_result["user"]["email"] == test_user_data["email"]

    def test_confirm_password_reset_invalid_token(self, test_db_session):
        """Test password reset with invalid token."""
        auth_service = AuthService(test_db_session)

        with pytest.raises(InvalidToken):
            auth_service.confirm_password_reset("invalid_token", "NewPass123!")

    def test_verify_token(self, test_db_session, test_user_data):
        """Test token verification."""
        auth_service = AuthService(test_db_session)

        # Register and get token
        login_result = auth_service.register(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )
        access_token = login_result["access_token"]

        # Verify token
        payload = auth_service.verify_token(access_token)

        assert payload["user_id"] is not None
        assert payload["email"] == test_user_data["email"]

    def test_verify_invalid_token(self, test_db_session):
        """Test verification of invalid token."""
        auth_service = AuthService(test_db_session)

        with pytest.raises(InvalidToken):
            auth_service.verify_token("invalid_token")

"""Tests for user service."""

import pytest
from authlib.services.user_service import UserService
from authlib.utils.exceptions import (
    UserNotFound,
    UserAlreadyExists,
    ValidationError,
)


class TestUserService:
    """Test cases for UserService."""

    def test_create_user(self, test_db_session, test_user_data):
        """Test creating a new user."""
        user_service = UserService(test_db_session)

        user = user_service.create_user(
            email=test_user_data["email"],
            password=test_user_data["password"],
            first_name=test_user_data["first_name"],
            last_name=test_user_data["last_name"],
        )

        assert user.id is not None
        assert user.email == test_user_data["email"]
        assert user.first_name == test_user_data["first_name"]
        assert user.last_name == test_user_data["last_name"]
        assert user.is_active
        assert not user.is_verified

    def test_create_duplicate_user(self, test_db_session, test_user_data):
        """Test creating a duplicate user."""
        user_service = UserService(test_db_session)

        # Create first user
        user_service.create_user(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )

        # Try to create duplicate
        with pytest.raises(UserAlreadyExists):
            user_service.create_user(
                email=test_user_data["email"],
                password=test_user_data["password"],
            )

    def test_create_user_invalid_email(self, test_db_session):
        """Test creating user with invalid email."""
        user_service = UserService(test_db_session)

        with pytest.raises(ValidationError):
            user_service.create_user(
                email="invalid-email",
                password="ValidPass123!",
            )

    def test_get_user_by_id(self, test_db_session, test_user_data):
        """Test getting user by ID."""
        user_service = UserService(test_db_session)

        created_user = user_service.create_user(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )

        retrieved_user = user_service.get_user_by_id(created_user.id)

        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.email == created_user.email

    def test_get_user_by_id_not_found(self, test_db_session):
        """Test getting user by non-existent ID."""
        user_service = UserService(test_db_session)

        user = user_service.get_user_by_id(9999)

        assert user is None

    def test_get_user_by_email(self, test_db_session, test_user_data):
        """Test getting user by email."""
        user_service = UserService(test_db_session)

        created_user = user_service.create_user(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )

        retrieved_user = user_service.get_user_by_email(test_user_data["email"])

        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id

    def test_get_user_by_email_case_insensitive(self, test_db_session, test_user_data):
        """Test getting user by email is case insensitive."""
        user_service = UserService(test_db_session)

        user_service.create_user(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )

        retrieved_user = user_service.get_user_by_email(test_user_data["email"].upper())

        assert retrieved_user is not None

    def test_get_user_by_email_not_found(self, test_db_session):
        """Test getting user by non-existent email."""
        user_service = UserService(test_db_session)

        user = user_service.get_user_by_email("nonexistent@example.com")

        assert user is None

    def test_get_all_users(self, test_db_session, test_user_data, test_user_data_2):
        """Test getting all users."""
        user_service = UserService(test_db_session)

        user_service.create_user(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )
        user_service.create_user(
            email=test_user_data_2["email"],
            password=test_user_data_2["password"],
        )

        users = user_service.get_all_users()

        assert len(users) == 2

    def test_update_user(self, test_db_session, test_user_data):
        """Test updating user."""
        user_service = UserService(test_db_session)

        user = user_service.create_user(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )

        updated_user = user_service.update_user(
            user_id=user.id,
            first_name="Updated",
            is_verified=True,
        )

        assert updated_user.first_name == "Updated"
        assert updated_user.is_verified

    def test_update_user_email(self, test_db_session, test_user_data):
        """Test updating user email."""
        user_service = UserService(test_db_session)

        user = user_service.create_user(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )

        new_email = "newemail@example.com"
        updated_user = user_service.update_user(
            user_id=user.id,
            email=new_email,
        )

        assert updated_user.email == new_email

    def test_update_user_not_found(self, test_db_session):
        """Test updating non-existent user."""
        user_service = UserService(test_db_session)

        with pytest.raises(UserNotFound):
            user_service.update_user(user_id=9999, first_name="Test")

    def test_change_password(self, test_db_session, test_user_data):
        """Test changing user password."""
        user_service = UserService(test_db_session)

        user = user_service.create_user(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )

        new_password = "NewPassword456!"
        updated_user = user_service.change_password(user.id, new_password)

        # Verify password was changed
        password_handler = user_service.password_handler
        assert password_handler.verify_password(new_password, updated_user.password_hash)
        assert not password_handler.verify_password(test_user_data["password"],
                                                     updated_user.password_hash)

    def test_delete_user(self, test_db_session, test_user_data):
        """Test deleting a user."""
        user_service = UserService(test_db_session)

        user = user_service.create_user(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )

        user_service.delete_user(user.id)

        # Verify user is deleted
        retrieved_user = user_service.get_user_by_id(user.id)
        assert retrieved_user is None

    def test_delete_user_not_found(self, test_db_session):
        """Test deleting non-existent user."""
        user_service = UserService(test_db_session)

        with pytest.raises(UserNotFound):
            user_service.delete_user(9999)

    def test_deactivate_user(self, test_db_session, test_user_data):
        """Test deactivating a user."""
        user_service = UserService(test_db_session)

        user = user_service.create_user(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )

        deactivated_user = user_service.deactivate_user(user.id)

        assert not deactivated_user.is_active

    def test_activate_user(self, test_db_session, test_user_data):
        """Test activating a user."""
        user_service = UserService(test_db_session)

        user = user_service.create_user(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )

        user_service.deactivate_user(user.id)
        activated_user = user_service.activate_user(user.id)

        assert activated_user.is_active

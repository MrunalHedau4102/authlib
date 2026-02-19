"""Tests for password utilities."""

import pytest
from authlib.utils.password import PasswordHandler
from authlib.utils.exceptions import ValidationError


class TestPasswordHandler:
    """Test cases for PasswordHandler."""

    def test_hash_password(self):
        """Test password hashing."""
        handler = PasswordHandler()
        password = "TestPassword123!"
        hashed = handler.hash_password(password)

        assert hashed != password
        assert len(hashed) > 0
        assert isinstance(hashed, str)

    def test_verify_password_valid(self):
        """Test password verification with valid password."""
        handler = PasswordHandler()
        password = "TestPassword123!"
        hashed = handler.hash_password(password)

        assert handler.verify_password(password, hashed)

    def test_verify_password_invalid(self):
        """Test password verification with invalid password."""
        handler = PasswordHandler()
        password = "TestPassword123!"
        hashed = handler.hash_password(password)

        assert not handler.verify_password("WrongPassword456!", hashed)

    def test_hash_password_empty_string(self):
        """Test password hashing with empty string."""
        handler = PasswordHandler()

        with pytest.raises(ValueError):
            handler.hash_password("")

    def test_hash_password_none(self):
        """Test password hashing with None."""
        handler = PasswordHandler()

        with pytest.raises(ValueError):
            handler.hash_password(None)

    def test_verify_password_empty(self):
        """Test password verification with empty password."""
        handler = PasswordHandler()

        with pytest.raises(ValueError):
            handler.verify_password("", "somehash")

    def test_verify_password_invalid_hash(self):
        """Test password verification with invalid hash."""
        handler = PasswordHandler()

        result = handler.verify_password("password", "invalid_hash")
        assert result is False

    def test_needs_rehashing(self):
        """Test needs_rehashing method."""
        handler = PasswordHandler(log_rounds=12)
        password = "TestPassword123!"
        hashed = handler.hash_password(password)

        # Hash doesn't need rehashing with same rounds
        assert not PasswordHandler.needs_rehashing(hashed, 12)

        # Hash needs rehashing with higher rounds
        assert PasswordHandler.needs_rehashing(hashed, 14)

    def test_different_hashes_same_password(self):
        """Test that same password produces different hashes (due to salt)."""
        handler = PasswordHandler()
        password = "TestPassword123!"

        hash1 = handler.hash_password(password)
        hash2 = handler.hash_password(password)

        assert hash1 != hash2  # Different salts
        assert handler.verify_password(password, hash1)
        assert handler.verify_password(password, hash2)

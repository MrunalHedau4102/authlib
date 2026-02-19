"""Tests for validators."""

import pytest
from authlib.utils.validators import EmailValidator, PasswordValidator
from authlib.utils.exceptions import ValidationError


class TestEmailValidator:
    """Test cases for EmailValidator."""

    def test_valid_email(self):
        """Test validation of valid email."""
        assert EmailValidator.validate("user@example.com")

    def test_valid_emails(self):
        """Test validation of various valid emails."""
        valid_emails = [
            "test@example.com",
            "user.name@example.com",
            "user+tag@example.co.uk",
            "123@example.com",
        ]

        for email in valid_emails:
            assert EmailValidator.validate(email)

    def test_invalid_email_no_at(self):
        """Test validation of email without @."""
        with pytest.raises(ValidationError):
            EmailValidator.validate("userexample.com")

    def test_invalid_email_no_domain(self):
        """Test validation of email without domain."""
        with pytest.raises(ValidationError):
            EmailValidator.validate("user@")

    def test_invalid_email_no_local_part(self):
        """Test validation of email without local part."""
        with pytest.raises(ValidationError):
            EmailValidator.validate("@example.com")

    def test_invalid_email_spaces(self):
        """Test validation of email with spaces."""
        with pytest.raises(ValidationError):
            EmailValidator.validate("user @example.com")

    def test_invalid_email_empty(self):
        """Test validation of empty email."""
        with pytest.raises(ValidationError):
            EmailValidator.validate("")

    def test_invalid_email_none(self):
        """Test validation of None email."""
        with pytest.raises(ValidationError):
            EmailValidator.validate(None)

    def test_email_too_long(self):
        """Test validation of email exceeding 254 chars."""
        long_email = "a" * 250 + "@example.com"
        with pytest.raises(ValidationError):
            EmailValidator.validate(long_email)

    def test_sanitize_email(self):
        """Test email sanitization."""
        email = "  USER@EXAMPLE.COM  "
        sanitized = EmailValidator.sanitize(email)

        assert sanitized == "user@example.com"


class TestPasswordValidator:
    """Test cases for PasswordValidator."""

    def test_valid_password(self):
        """Test validation of valid password."""
        assert PasswordValidator.validate("ValidPass123!")

    def test_valid_passwords(self):
        """Test validation of various valid passwords."""
        valid_passwords = [
            "SecurePass123!",
            "MyP@ssw0rd",
            "Complex#Pwd2024",
            "TestPassword321$",
        ]

        for password in valid_passwords:
            assert PasswordValidator.validate(password)

    def test_password_too_short(self):
        """Test validation of password that's too short."""
        with pytest.raises(ValidationError):
            PasswordValidator.validate("Short1!")

    def test_password_no_uppercase(self):
        """Test validation of password without uppercase."""
        with pytest.raises(ValidationError):
            PasswordValidator.validate("lowercase123!")

    def test_password_no_lowercase(self):
        """Test validation of password without lowercase."""
        with pytest.raises(ValidationError):
            PasswordValidator.validate("UPPERCASE123!")

    def test_password_no_digits(self):
        """Test validation of password without digits."""
        with pytest.raises(ValidationError):
            PasswordValidator.validate("OnlyLetters!")

    def test_password_no_special(self):
        """Test validation of password without special characters."""
        with pytest.raises(ValidationError):
            PasswordValidator.validate("NoSpecial123")

    def test_password_empty(self):
        """Test validation of empty password."""
        with pytest.raises(ValidationError):
            PasswordValidator.validate("")

    def test_password_none(self):
        """Test validation of None password."""
        with pytest.raises(ValidationError):
            PasswordValidator.validate(None)

    def test_check_password_strength_valid(self):
        """Test password strength check for valid password."""
        result = PasswordValidator.check_strength("ValidPass123!")

        assert result["is_valid"]
        assert result["score"] == 100
        assert len(result["issues"]) == 0

    def test_check_password_strength_weak(self):
        """Test password strength check for weak password."""
        result = PasswordValidator.check_strength("short!")

        assert not result["is_valid"]
        assert result["score"] < 100
        assert len(result["issues"]) > 0

    def test_check_password_strength_feedback(self):
        """Test password strength feedback."""
        result = PasswordValidator.check_strength("password")

        assert not result["is_valid"]
        assert "uppercase" in result["issues"][0].lower() or \
               "digit" in result["issues"][0].lower() or \
               "special" in result["issues"][0].lower()

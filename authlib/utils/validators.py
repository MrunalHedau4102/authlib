"""Input validation utilities."""

import re
from authlib.utils.exceptions import ValidationError


class EmailValidator:
    """Validates email addresses."""

    # RFC 5322 simplified email regex
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )

    @classmethod
    def validate(cls, email: str) -> bool:
        """
        Validate email format.

        Args:
            email: Email address to validate

        Returns:
            True if valid, False otherwise

        Raises:
            ValidationError: If email is invalid
        """
        if not email or not isinstance(email, str):
            raise ValidationError("Email must be a non-empty string")

        email = email.strip().lower()

        if len(email) > 254:
            raise ValidationError("Email is too long (max 254 characters)")

        if not cls.EMAIL_PATTERN.match(email):
            raise ValidationError("Invalid email format")

        return True

    @classmethod
    def sanitize(cls, email: str) -> str:
        """
        Sanitize email address.

        Args:
            email: Email address to sanitize

        Returns:
            Sanitized email address
        """
        return email.strip().lower()


class PasswordValidator:
    """Validates password strength."""

    MIN_LENGTH = 8
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGITS = True
    REQUIRE_SPECIAL = True

    @classmethod
    def validate(cls, password: str) -> bool:
        """
        Validate password strength.

        Args:
            password: Password to validate

        Returns:
            True if valid, False otherwise

        Raises:
            ValidationError: If password doesn't meet requirements
        """
        if not password or not isinstance(password, str):
            raise ValidationError("Password must be a non-empty string")

        if len(password) < cls.MIN_LENGTH:
            raise ValidationError(
                f"Password must be at least {cls.MIN_LENGTH} characters long"
            )

        if cls.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            raise ValidationError(
                "Password must contain at least one uppercase letter"
            )

        if cls.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            raise ValidationError(
                "Password must contain at least one lowercase letter"
            )

        if cls.REQUIRE_DIGITS and not re.search(r'\d', password):
            raise ValidationError("Password must contain at least one digit")

        if cls.REQUIRE_SPECIAL and not re.search(
            r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]',
            password
        ):
            raise ValidationError(
                "Password must contain at least one special character"
            )

        return True

    @classmethod
    def check_strength(cls, password: str) -> dict:
        """
        Check password strength and return detailed feedback.

        Args:
            password: Password to check

        Returns:
            Dictionary with strength details
        """
        feedback = {
            "is_valid": False,
            "score": 0,
            "issues": [],
        }

        if not password or not isinstance(password, str):
            feedback["issues"].append("Password must be a non-empty string")
            return feedback

        score = 0

        # Length check
        if len(password) >= cls.MIN_LENGTH:
            score += 20
        else:
            feedback["issues"].append(
                f"At least {cls.MIN_LENGTH} characters required"
            )

        # Uppercase check
        if re.search(r'[A-Z]', password):
            score += 20
        else:
            feedback["issues"].append("Add uppercase letters")

        # Lowercase check
        if re.search(r'[a-z]', password):
            score += 20
        else:
            feedback["issues"].append("Add lowercase letters")

        # Digits check
        if re.search(r'\d', password):
            score += 20
        else:
            feedback["issues"].append("Add digits")

        # Special characters check
        if re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', password):
            score += 20
        else:
            feedback["issues"].append("Add special characters")

        feedback["score"] = score
        feedback["is_valid"] = len(feedback["issues"]) == 0

        return feedback

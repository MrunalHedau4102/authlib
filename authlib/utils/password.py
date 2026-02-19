"""Password hashing and verification utilities."""

import bcrypt
from authlib.config import Config


class PasswordHandler:
    """Handles password hashing and verification using bcrypt."""

    def __init__(self, log_rounds: int = None) -> None:
        """
        Initialize PasswordHandler.

        Args:
            log_rounds: Bcrypt log rounds (cost factor)
        """
        config = Config()
        self.log_rounds = log_rounds or config.BCRYPT_LOG_ROUNDS

    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt.

        Args:
            password: Plain text password to hash

        Returns:
            Hashed password bytes

        Raises:
            ValueError: If password is invalid
        """
        if not password or not isinstance(password, str):
            raise ValueError("Password must be a non-empty string")

        # Encode password to bytes
        password_bytes = password.encode('utf-8')

        # Generate salt and hash
        salt = bcrypt.gensalt(rounds=self.log_rounds)
        hashed = bcrypt.hashpw(password_bytes, salt)

        # Return as string
        return hashed.decode('utf-8')

    def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.

        Args:
            password: Plain text password to verify
            hashed_password: Hashed password to compare against

        Returns:
            True if password matches, False otherwise

        Raises:
            ValueError: If inputs are invalid
        """
        if not password or not isinstance(password, str):
            raise ValueError("Password must be a non-empty string")

        if not hashed_password or not isinstance(hashed_password, str):
            raise ValueError("Hashed password must be a non-empty string")

        try:
            # Encode inputs to bytes
            password_bytes = password.encode('utf-8')
            hashed_bytes = hashed_password.encode('utf-8')

            # Verify using bcrypt
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except ValueError:
            # bcrypt raises ValueError for invalid hash
            return False

    @staticmethod
    def needs_rehashing(hashed_password: str, log_rounds: int = None) -> bool:
        """
        Check if a hashed password needs to be rehashed (e.g., if log_rounds increased).

        Args:
            hashed_password: Hashed password to check
            log_rounds: Current log rounds setting

        Returns:
            True if rehashing is recommended, False otherwise
        """
        if not hashed_password:
            return True

        try:
            config = Config()
            current_rounds = log_rounds or config.BCRYPT_LOG_ROUNDS

            # Extract rounds from bcrypt hash (format: $2b$XX$...)
            # Hash format: $2b$12$...
            hash_rounds = int(hashed_password.split('$')[2])
            return hash_rounds < current_rounds
        except (IndexError, ValueError):
            return True

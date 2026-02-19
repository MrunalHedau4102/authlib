"""JWT token handling utilities."""

from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Any
import jwt
from authlib.config import Config
from authlib.utils.exceptions import InvalidToken


class JWTHandler:
    """Handles JWT token creation and validation."""

    def __init__(self, config: Config = None) -> None:
        """
        Initialize JWTHandler.

        Args:
            config: Config object (uses default if not provided)
        """
        self.config = config or Config()
        self.secret_key = self.config.JWT_SECRET_KEY
        self.algorithm = self.config.JWT_ALGORITHM
        self.access_token_expiry = self.config.JWT_ACCESS_TOKEN_EXPIRY_MINUTES
        self.refresh_token_expiry = self.config.JWT_REFRESH_TOKEN_EXPIRY_DAYS

    def create_access_token(
        self,
        user_id: int,
        email: str,
        additional_claims: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a JWT access token.

        Args:
            user_id: User ID for the token
            email: User email for the token
            additional_claims: Optional additional claims to include

        Returns:
            Encoded JWT token string

        Raises:
            ValueError: If user_id or email is invalid
        """
        if not user_id or not isinstance(user_id, int):
            raise ValueError("user_id must be a positive integer")

        if not email or not isinstance(email, str):
            raise ValueError("email must be a non-empty string")

        now = datetime.now(timezone.utc)
        expiry = now + timedelta(minutes=self.access_token_expiry)

        payload = {
            "user_id": user_id,
            "email": email,
            "token_type": "access",
            "iat": now,
            "exp": expiry,
        }

        if additional_claims:
            payload.update(additional_claims)

        token = jwt.encode(
            payload,
            self.secret_key,
            algorithm=self.algorithm,
        )

        return token

    def create_refresh_token(
        self,
        user_id: int,
        email: str,
        additional_claims: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a JWT refresh token.

        Args:
            user_id: User ID for the token
            email: User email for the token
            additional_claims: Optional additional claims to include

        Returns:
            Encoded JWT token string

        Raises:
            ValueError: If user_id or email is invalid
        """
        if not user_id or not isinstance(user_id, int):
            raise ValueError("user_id must be a positive integer")

        if not email or not isinstance(email, str):
            raise ValueError("email must be a non-empty string")

        now = datetime.now(timezone.utc)
        expiry = now + timedelta(days=self.refresh_token_expiry)

        payload = {
            "user_id": user_id,
            "email": email,
            "token_type": "refresh",
            "iat": now,
            "exp": expiry,
        }

        if additional_claims:
            payload.update(additional_claims)

        token = jwt.encode(
            payload,
            self.secret_key,
            algorithm=self.algorithm,
        )

        return token

    def create_password_reset_token(
        self,
        user_id: int,
        email: str,
        additional_claims: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a password reset token.

        Args:
            user_id: User ID for the token
            email: User email for the token
            additional_claims: Optional additional claims to include

        Returns:
            Encoded JWT token string

        Raises:
            ValueError: If user_id or email is invalid
        """
        if not user_id or not isinstance(user_id, int):
            raise ValueError("user_id must be a positive integer")

        if not email or not isinstance(email, str):
            raise ValueError("email must be a non-empty string")

        now = datetime.now(timezone.utc)
        expiry = now + timedelta(
            minutes=self.config.PASSWORD_RESET_TOKEN_EXPIRY_MINUTES
        )

        payload = {
            "user_id": user_id,
            "email": email,
            "token_type": "password_reset",
            "iat": now,
            "exp": expiry,
        }

        if additional_claims:
            payload.update(additional_claims)

        token = jwt.encode(
            payload,
            self.secret_key,
            algorithm=self.algorithm,
        )

        return token

    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode a JWT token.

        Args:
            token: JWT token to verify

        Returns:
            Decoded token payload

        Raises:
            InvalidToken: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise InvalidToken("Token has expired")
        except jwt.InvalidTokenError as e:
            raise InvalidToken(f"Invalid token: {str(e)}")

    def verify_access_token(self, token: str) -> Dict[str, Any]:
        """
        Verify an access token and check token type.

        Args:
            token: JWT token to verify

        Returns:
            Decoded token payload

        Raises:
            InvalidToken: If token is invalid, expired, or not an access token
        """
        payload = self.verify_token(token)

        if payload.get("token_type") != "access":
            raise InvalidToken("Token is not an access token")

        return payload

    def verify_refresh_token(self, token: str) -> Dict[str, Any]:
        """
        Verify a refresh token and check token type.

        Args:
            token: JWT token to verify

        Returns:
            Decoded token payload

        Raises:
            InvalidToken: If token is invalid, expired, or not a refresh token
        """
        payload = self.verify_token(token)

        if payload.get("token_type") != "refresh":
            raise InvalidToken("Token is not a refresh token")

        return payload

    def verify_password_reset_token(self, token: str) -> Dict[str, Any]:
        """
        Verify a password reset token and check token type.

        Args:
            token: JWT token to verify

        Returns:
            Decoded token payload

        Raises:
            InvalidToken: If token is invalid, expired, or not a password reset token
        """
        payload = self.verify_token(token)

        if payload.get("token_type") != "password_reset":
            raise InvalidToken("Token is not a password reset token")

        return payload

    def get_user_id_from_token(self, token: str) -> int:
        """
        Extract user ID from a token without full verification.

        Args:
            token: JWT token

        Returns:
            User ID

        Raises:
            InvalidToken: If token is invalid
        """
        try:
            # Decode without verification for faster extraction
            # In production, always verify first
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
            )
            return payload.get("user_id")
        except jwt.InvalidTokenError as e:
            raise InvalidToken(f"Invalid token: {str(e)}")

    def get_expiry_time(self, token: str) -> datetime:
        """
        Get token expiration time.

        Args:
            token: JWT token

        Returns:
            Expiration datetime

        Raises:
            InvalidToken: If token is invalid
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": False},  # Don't validate expiry for this check
            )
            exp_timestamp = payload.get("exp")
            if exp_timestamp:
                return datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
            raise InvalidToken("Token has no expiration time")
        except jwt.InvalidTokenError as e:
            raise InvalidToken(f"Invalid token: {str(e)}")

    def is_token_expired(self, token: str) -> bool:
        """
        Check if a token is expired.

        Args:
            token: JWT token

        Returns:
            True if expired, False otherwise
        """
        try:
            self.verify_token(token)
            return False
        except InvalidToken:
            return True

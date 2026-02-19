"""Authentication service."""

from typing import Dict, Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from authlib.models.user import User
from authlib.models.token_blacklist import TokenBlacklist
from authlib.services.user_service import UserService
from authlib.utils.jwt_handler import JWTHandler
from authlib.utils.password import PasswordHandler
from authlib.utils.validators import EmailValidator, PasswordValidator
from authlib.utils.exceptions import (
    UserNotFound,
    InvalidCredentials,
    InvalidToken,
    UserAlreadyExists,
    ValidationError,
    DatabaseError,
)
from authlib.config import Config


class AuthService:
    """Service for authentication operations."""

    def __init__(self, session: Session, config: Config = None) -> None:
        """
        Initialize AuthService.

        Args:
            session: SQLAlchemy database session
            config: Config object (uses default if not provided)
        """
        self.session = session
        self.config = config or Config()
        self.jwt_handler = JWTHandler(config)
        self.password_handler = PasswordHandler()
        self.user_service = UserService(session)

    def register(
        self,
        email: str,
        password: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> Dict[str, any]:
        """
        Register a new user.

        Args:
            email: User email
            password: User password
            first_name: User's first name (optional)
            last_name: User's last name (optional)

        Returns:
            Dictionary with user and tokens

        Raises:
            ValidationError: If email or password is invalid
            UserAlreadyExists: If user already exists
            DatabaseError: If database operation fails
        """
        # Validate email and password
        EmailValidator.validate(email)
        PasswordValidator.validate(password)

        # Create user
        user = self.user_service.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        # Generate tokens
        tokens = self._generate_tokens(user)

        return {
            "user": user.to_dict(),
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": "Bearer",
        }

    def login(self, email: str, password: str) -> Dict[str, any]:
        """
        Authenticate user and return tokens.

        Args:
            email: User email
            password: User password

        Returns:
            Dictionary with user and tokens

        Raises:
            UserNotFound: If user doesn't exist
            InvalidCredentials: If password is wrong
            DatabaseError: If database operation fails
        """
        # Validate inputs
        EmailValidator.validate(email)
        email = EmailValidator.sanitize(email)

        # Get user
        user = self.user_service.get_user_by_email(email)
        if not user:
            raise UserNotFound(f"User with email {email} not found")

        # Check if user is active
        if not user.is_active:
            raise InvalidCredentials("User account is disabled")

        # Verify password
        if not self.password_handler.verify_password(password, user.password_hash):
            raise InvalidCredentials("Invalid email or password")

        # Update last login
        user.update_last_login(self.session)

        # Generate tokens
        tokens = self._generate_tokens(user)

        return {
            "user": user.to_dict(),
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": "Bearer",
        }

    def refresh_access_token(self, refresh_token: str) -> Dict[str, str]:
        """
        Generate a new access token using a refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            Dictionary with new access token

        Raises:
            InvalidToken: If refresh token is invalid
            UserNotFound: If user doesn't exist
        """
        # Verify refresh token
        payload = self.jwt_handler.verify_refresh_token(refresh_token)
        user_id = payload.get("user_id")

        # Get user
        user = self.user_service.get_user_by_id(user_id)
        if not user:
            raise UserNotFound(f"User with ID {user_id} not found")

        # Check if token is blacklisted
        if self._is_token_blacklisted(refresh_token):
            raise InvalidToken("Refresh token has been revoked")

        # Create new access token
        access_token = self.jwt_handler.create_access_token(
            user_id=user.id,
            email=user.email,
        )

        return {
            "access_token": access_token,
            "token_type": "Bearer",
        }

    def logout(self, token: str, token_type: str = "access") -> None:
        """
        Logout user by blacklisting token.

        Args:
            token: JWT token to blacklist
            token_type: Type of token ('access' or 'refresh')

        Raises:
            InvalidToken: If token is invalid
            DatabaseError: If database operation fails
        """
        # Verify and decode token
        if token_type == "access":
            payload = self.jwt_handler.verify_access_token(token)
        elif token_type == "refresh":
            payload = self.jwt_handler.verify_refresh_token(token)
        else:
            raise ValidationError(f"Unknown token type: {token_type}")

        # Add to blacklist
        self._blacklist_token(
            token=token,
            user_id=payload.get("user_id"),
            token_type=token_type,
            reason="User logout",
        )

    def request_password_reset(self, email: str) -> Dict[str, str]:
        """
        Generate password reset token.

        Args:
            email: User email

        Returns:
            Dictionary with reset token

        Raises:
            UserNotFound: If user doesn't exist
        """
        # Validate email
        EmailValidator.validate(email)
        email = EmailValidator.sanitize(email)

        # Get user
        user = self.user_service.get_user_by_email(email)
        if not user:
            raise UserNotFound(f"User with email {email} not found")

        # Generate reset token
        reset_token = self.jwt_handler.create_password_reset_token(
            user_id=user.id,
            email=user.email,
        )

        return {
            "reset_token": reset_token,
            "token_type": "Bearer",
            "expires_in": self.config.PASSWORD_RESET_TOKEN_EXPIRY_MINUTES * 60,
        }

    def confirm_password_reset(self, reset_token: str, new_password: str) -> Dict[str, any]:
        """
        Reset user password using reset token.

        Args:
            reset_token: Valid password reset token
            new_password: New password

        Returns:
            Dictionary with user and tokens

        Raises:
            InvalidToken: If reset token is invalid
            ValidationError: If password is invalid
            UserNotFound: If user doesn't exist
            DatabaseError: If database operation fails
        """
        # Verify reset token
        payload = self.jwt_handler.verify_password_reset_token(reset_token)
        user_id = payload.get("user_id")

        # Validate new password
        PasswordValidator.validate(new_password)

        # Get user
        user = self.user_service.get_user_by_id(user_id)
        if not user:
            raise UserNotFound(f"User with ID {user_id} not found")

        # Change password
        user = self.user_service.change_password(user_id, new_password)

        # Blacklist reset token
        self._blacklist_token(
            token=reset_token,
            user_id=user_id,
            token_type="password_reset",
            reason="Password reset completed",
        )

        # Generate new tokens
        tokens = self._generate_tokens(user)

        return {
            "user": user.to_dict(),
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": "Bearer",
        }

    def verify_token(self, token: str) -> Dict[str, any]:
        """
        Verify and decode a token.

        Args:
            token: JWT token

        Returns:
            Decoded token payload

        Raises:
            InvalidToken: If token is invalid
        """
        # Verify token
        payload = self.jwt_handler.verify_access_token(token)

        # Check if blacklisted
        if self._is_token_blacklisted(token):
            raise InvalidToken("Token has been revoked")

        return payload

    def _generate_tokens(self, user: User) -> Dict[str, str]:
        """
        Generate access and refresh tokens for a user.

        Args:
            user: User object

        Returns:
            Dictionary with tokens
        """
        access_token = self.jwt_handler.create_access_token(
            user_id=user.id,
            email=user.email,
        )

        refresh_token = self.jwt_handler.create_refresh_token(
            user_id=user.id,
            email=user.email,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    def _blacklist_token(
        self,
        token: str,
        user_id: int,
        token_type: str,
        reason: Optional[str] = None,
    ) -> None:
        """
        Add a token to the blacklist.

        Args:
            token: JWT token
            user_id: User ID
            token_type: Type of token
            reason: Reason for blacklisting (optional)

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Get token expiration
            exp_time = self.jwt_handler.get_expiry_time(token)

            # Create blacklist entry
            blacklist_entry = TokenBlacklist(
                jti=token,
                user_id=user_id,
                token_type=token_type,
                reason=reason,
                expires_at=exp_time,
            )

            self.session.add(blacklist_entry)
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f"Failed to blacklist token: {str(e)}") from e

    def _is_token_blacklisted(self, token: str) -> bool:
        """
        Check if a token is blacklisted.

        Args:
            token: JWT token

        Returns:
            True if blacklisted, False otherwise
        """
        try:
            blacklist_entry = (
                self.session.query(TokenBlacklist)
                .filter(TokenBlacklist.jti == token)
                .first()
            )
            return blacklist_entry is not None
        except SQLAlchemyError:
            return False

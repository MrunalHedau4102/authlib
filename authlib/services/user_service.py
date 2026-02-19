"""User management service."""

from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from authlib.models.user import User
from authlib.utils.password import PasswordHandler
from authlib.utils.validators import EmailValidator
from authlib.utils.exceptions import (
    UserNotFound,
    UserAlreadyExists,
    ValidationError,
    DatabaseError,
)


class UserService:
    """Service for user-related operations."""

    def __init__(self, session: Session) -> None:
        """
        Initialize UserService.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session
        self.password_handler = PasswordHandler()

    def create_user(
        self,
        email: str,
        password: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> User:
        """
        Create a new user.

        Args:
            email: User email address
            password: Plain text password
            first_name: User's first name (optional)
            last_name: User's last name (optional)

        Returns:
            Created User object

        Raises:
            ValidationError: If email or password is invalid
            UserAlreadyExists: If user with email already exists
            DatabaseError: If database operation fails
        """
        # Validate email
        EmailValidator.validate(email)
        email = EmailValidator.sanitize(email)

        # Check if user already exists
        existing_user = self.get_user_by_email(email)
        if existing_user:
            raise UserAlreadyExists(
                f"User with email {email} already exists"
            )

        # Hash password
        password_hash = self.password_handler.hash_password(password)

        try:
            # Create user
            user = User(
                email=email,
                password_hash=password_hash,
                first_name=first_name,
                last_name=last_name,
                is_active=True,
                is_verified=False,
            )

            self.session.add(user)
            self.session.commit()
            self.session.refresh(user)

            return user
        except IntegrityError as e:
            self.session.rollback()
            raise UserAlreadyExists("User with this email already exists") from e
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f"Failed to create user: {str(e)}") from e

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User object if found, None otherwise

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            user = self.session.query(User).filter(User.id == user_id).first()
            return user
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to retrieve user: {str(e)}") from e

    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email.

        Args:
            email: User email address

        Returns:
            User object if found, None otherwise

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            email = EmailValidator.sanitize(email)
            user = self.session.query(User).filter(User.email == email).first()
            return user
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to retrieve user: {str(e)}") from e

    def get_all_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get all users with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of User objects

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            users = self.session.query(User).offset(skip).limit(limit).all()
            return users
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to retrieve users: {str(e)}") from e

    def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get all active users with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of active User objects

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            users = (
                self.session.query(User)
                .filter(User.is_active == True)
                .offset(skip)
                .limit(limit)
                .all()
            )
            return users
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to retrieve users: {str(e)}") from e

    def update_user(
        self,
        user_id: int,
        email: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_verified: Optional[bool] = None,
    ) -> User:
        """
        Update user information.

        Args:
            user_id: User ID
            email: New email (optional)
            first_name: New first name (optional)
            last_name: New last name (optional)
            is_active: New active status (optional)
            is_verified: New verified status (optional)

        Returns:
            Updated User object

        Raises:
            UserNotFound: If user doesn't exist
            ValidationError: If email is invalid
            DatabaseError: If database operation fails
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise UserNotFound(f"User with ID {user_id} not found")

        try:
            if email is not None:
                EmailValidator.validate(email)
                email = EmailValidator.sanitize(email)
                user.email = email

            if first_name is not None:
                user.first_name = first_name

            if last_name is not None:
                user.last_name = last_name

            if is_active is not None:
                user.is_active = is_active

            if is_verified is not None:
                user.is_verified = is_verified

            user.updated_at = datetime.now(timezone.utc)

            self.session.commit()
            self.session.refresh(user)

            return user
        except IntegrityError as e:
            self.session.rollback()
            raise UserAlreadyExists("User with this email already exists") from e
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f"Failed to update user: {str(e)}") from e

    def change_password(self, user_id: int, new_password: str) -> User:
        """
        Change user password.

        Args:
            user_id: User ID
            new_password: New password

        Returns:
            Updated User object

        Raises:
            UserNotFound: If user doesn't exist
            DatabaseError: If database operation fails
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise UserNotFound(f"User with ID {user_id} not found")

        try:
            password_hash = self.password_handler.hash_password(new_password)
            user.password_hash = password_hash
            user.updated_at = datetime.now(timezone.utc)

            self.session.commit()
            self.session.refresh(user)

            return user
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f"Failed to change password: {str(e)}") from e

    def delete_user(self, user_id: int) -> None:
        """
        Delete a user.

        Args:
            user_id: User ID

        Raises:
            UserNotFound: If user doesn't exist
            DatabaseError: If database operation fails
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise UserNotFound(f"User with ID {user_id} not found")

        try:
            self.session.delete(user)
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f"Failed to delete user: {str(e)}") from e

    def verify_user(self, user_id: int) -> User:
        """
        Mark user as verified.

        Args:
            user_id: User ID

        Returns:
            Updated User object

        Raises:
            UserNotFound: If user doesn't exist
            DatabaseError: If database operation fails
        """
        return self.update_user(user_id, is_verified=True)

    def deactivate_user(self, user_id: int) -> User:
        """
        Deactivate a user.

        Args:
            user_id: User ID

        Returns:
            Updated User object

        Raises:
            UserNotFound: If user doesn't exist
            DatabaseError: If database operation fails
        """
        return self.update_user(user_id, is_active=False)

    def activate_user(self, user_id: int) -> User:
        """
        Activate a user.

        Args:
            user_id: User ID

        Returns:
            Updated User object

        Raises:
            UserNotFound: If user doesn't exist
            DatabaseError: If database operation fails
        """
        return self.update_user(user_id, is_active=True)

    def user_exists(self, email: str) -> bool:
        """
        Check if user exists by email.

        Args:
            email: User email address

        Returns:
            True if user exists, False otherwise
        """
        try:
            email = EmailValidator.sanitize(email)
            user = self.session.query(User).filter(User.email == email).first()
            return user is not None
        except (SQLAlchemyError, ValidationError):
            return False

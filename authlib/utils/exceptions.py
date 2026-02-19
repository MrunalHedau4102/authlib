"""Custom exception classes for AuthLib."""


class AuthException(Exception):
    """Base exception for authentication errors."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        """
        Initialize AuthException.

        Args:
            message: Error message
            status_code: HTTP status code
        """
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class UserNotFound(AuthException):
    """Raised when user is not found."""

    def __init__(self, message: str = "User not found") -> None:
        super().__init__(message, status_code=404)


class InvalidCredentials(AuthException):
    """Raised when credentials are invalid."""

    def __init__(self, message: str = "Invalid email or password") -> None:
        super().__init__(message, status_code=401)


class InvalidToken(AuthException):
    """Raised when token is invalid or expired."""

    def __init__(self, message: str = "Invalid or expired token") -> None:
        super().__init__(message, status_code=401)


class UserAlreadyExists(AuthException):
    """Raised when user already exists."""

    def __init__(self, message: str = "User with this email already exists") -> None:
        super().__init__(message, status_code=409)


class ValidationError(AuthException):
    """Raised when validation fails."""

    def __init__(self, message: str = "Validation failed") -> None:
        super().__init__(message, status_code=400)


class DatabaseError(AuthException):
    """Raised when database operation fails."""

    def __init__(self, message: str = "Database operation failed") -> None:
        super().__init__(message, status_code=500)


class EmailSendError(AuthException):
    """Raised when email sending fails."""

    def __init__(self, message: str = "Failed to send email") -> None:
        super().__init__(message, status_code=500)

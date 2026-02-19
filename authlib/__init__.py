"""
AuthLib - A scalable, framework-agnostic Python authentication library.
Provides signup, login, JWT token management, and password reset functionality.
"""

__version__ = "1.0.0"
__author__ = "AuthLib Contributors"

from authlib.config import Config
from authlib.services.auth_service import AuthService
from authlib.services.user_service import UserService
from authlib.models.user import User
from authlib.utils.exceptions import (
    AuthException,
    UserNotFound,
    InvalidCredentials,
    InvalidToken,
    UserAlreadyExists,
)

__all__ = [
    "Config",
    "AuthService",
    "UserService",
    "User",
    "AuthException",
    "UserNotFound",
    "InvalidCredentials",
    "InvalidToken",
    "UserAlreadyExists",
]

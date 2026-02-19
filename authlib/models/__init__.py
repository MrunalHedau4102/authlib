"""Database models for authentication."""

from authlib.models.user import User
from authlib.models.token_blacklist import TokenBlacklist

__all__ = ["User", "TokenBlacklist"]

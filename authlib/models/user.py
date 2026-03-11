"""User database model."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Index
from authlib.database import Base
import pyotp


class User(Base):
    """User model for authentication system."""

    __tablename__ = "users"

    # Columns
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(254), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_two_factor_enabled = Column(Boolean, default=False, nullable=False)
    two_factor_secret = Column(String(32), nullable=True, index=True)
    otp_verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Indexes
    __table_args__ = (
        Index("idx_user_email", "email"),
        Index("idx_user_is_active", "is_active"),
        Index("idx_user_two_factor_secret", "two_factor_secret"),
    )

    def __repr__(self) -> str:
        """String representation of User."""
        return f"<User(id={self.id}, email={self.email}, is_active={self.is_active})>"

    def to_dict(self) -> dict:
        """Convert User to dictionary."""
        return {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_two_factor_enabled": self.is_two_factor_enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }

    def get_full_name(self) -> str:
        """Get user's full name."""
        name_parts = []
        if self.first_name:
            name_parts.append(self.first_name)
        if self.last_name:
            name_parts.append(self.last_name)
        return " ".join(name_parts) if name_parts else self.email

    def update_last_login(self, session=None) -> None:
        """Update last login timestamp."""
        self.last_login = datetime.now(timezone.utc)
        if session:
            session.commit()

    def enable_2fa(self, secret: str) -> None:
        """Enable two-factor authentication for user.

        Args:
            secret: Base32-encoded TOTP secret
        """
        self.two_factor_secret = secret
        self.is_two_factor_enabled = True
        self.otp_verified_at = datetime.now(timezone.utc)

    def disable_2fa(self) -> None:
        """Disable two-factor authentication for user."""
        self.two_factor_secret = None
        self.is_two_factor_enabled = False
        self.otp_verified_at = None

    def get_otp_auth_uri(self) -> str:
        """Generate otpauth URI for QR code scanning.

        Returns:
            otpauth:// URI string for use with authenticator apps

        Raises:
            ValueError: If two_factor_secret is not set
        """
        if not self.two_factor_secret:
            raise ValueError("Two-factor secret not set")

        totp = pyotp.TOTP(self.two_factor_secret)
        return totp.provisioning_uri(
            name=self.email,
            issuer_name="AuthLib"
        )

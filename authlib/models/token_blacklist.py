"""Token blacklist model for token revocation."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Index
from authlib.database import Base


class TokenBlacklist(Base):
    """Model for storing revoked tokens."""

    __tablename__ = "token_blacklist"

    # Columns
    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String(500), unique=True, nullable=False, index=True)  # JWT ID
    user_id = Column(Integer, nullable=False, index=True)
    token_type = Column(String(50), nullable=False)  # 'access', 'refresh', etc.
    reason = Column(String(255), nullable=True)  # Reason for revocation (logout, password reset, etc.)
    revoked_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
    )  # Token expiration time

    # Indexes
    __table_args__ = (
        Index("idx_token_blacklist_jti", "jti"),
        Index("idx_token_blacklist_user_id", "user_id"),
        Index("idx_token_blacklist_expires_at", "expires_at"),
    )

    def __repr__(self) -> str:
        """String representation of TokenBlacklist."""
        return f"<TokenBlacklist(id={self.id}, user_id={self.user_id}, token_type={self.token_type})>"

    def to_dict(self) -> dict:
        """Convert TokenBlacklist to dictionary."""
        return {
            "id": self.id,
            "jti": self.jti,
            "user_id": self.user_id,
            "token_type": self.token_type,
            "reason": self.reason,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }

    @property
    def is_expired(self) -> bool:
        """Check if blacklist entry is expired."""
        return datetime.now(timezone.utc) > self.expires_at

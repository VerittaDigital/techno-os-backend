"""SQLAlchemy model for sessions (F2.3 Bearer token persistence)."""

from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Index
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class SessionModel(Base):
    """
    Session table for F2.3 Bearer token authentication.
    
    Invariants:
    - session_id is UUID (primary key)
    - user_id is bound to api_key_hash (immutable after creation)
    - expires_at is absolute TTL (8h default, no sliding window)
    - revoked_at != NULL means session is revoked
    - All timestamps are UTC, timezone-aware
    """
    
    __tablename__ = "sessions"
    
    # Primary key
    session_id = Column(
        String(36),  # UUID v4 = 36 chars
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    
    # Binding: session ↔ user ↔ api_key
    user_id = Column(String(255), nullable=False, index=True)
    api_key_hash = Column(String(64), nullable=False, index=True)  # SHA256
    
    # Timestamps (stored as UTC in DB, always assume UTC when reading)
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )
    expires_at = Column(
        DateTime,
        nullable=False,
    )
    revoked_at = Column(
        DateTime,
        nullable=True,
        default=None,
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )
    
    # Composite index for efficient expiry cleanup
    __table_args__ = (
        Index("ix_sessions_expires_at", "expires_at"),
        Index("ix_sessions_user_api_key", "user_id", "api_key_hash"),
    )
    
    def is_valid(self) -> bool:
        """Check if session is valid (not expired, not revoked)."""
        # DB timestamps are naive UTC; convert current time to naive UTC for comparison
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        return (
            self.revoked_at is None
            and self.expires_at > now
        )
    
    def is_revoked(self) -> bool:
        """Check if session is revoked."""
        return self.revoked_at is not None
    
    def is_expired(self) -> bool:
        """Check if session is expired."""
        # DB timestamps are naive UTC; convert current time to naive UTC for comparison
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        return self.expires_at <= now
    
    def __repr__(self) -> str:
        return (
            f"Session(id={self.session_id[:8]}..., "
            f"user={self.user_id}, "
            f"valid={self.is_valid()})"
        )

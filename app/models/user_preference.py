"""SQLAlchemy model for user preferences (F9.9-A).

Preferences are explicit state set by the user, never inferred.
Schema preserves existing wide-column structure (1:1 user→preferences).
"""

from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Index
from sqlalchemy.sql import func
from app.models.session import Base


class UserPreference(Base):
    """
    User preferences table (wide-column, 1:1 with user_id).
    
    Invariants:
    - user_id is unique (one preference record per user)
    - user_id format: u_[a-z0-9]{8} (validated by F2.3 gate)
    - preferences are optional (nullable columns)
    - created_at is immutable (set on insert)
    - updated_at is automatic (updated on modification)
    
    Privacy:
    - No logging of preference values (V-COF privacy-by-design)
    - User controls all preferences explicitly
    """
    
    __tablename__ = "user_preferences"
    
    # Primary key
    preference_id = Column(
        String(36),  # UUID v4 = 36 chars
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    
    # User identifier (validated by F2.3 gate, format: u_[a-z0-9]{8})
    user_id = Column(String(255), nullable=False, unique=True, index=True)
    
    # Preference fields (nullable = user hasn't set yet)
    tone_preference = Column(String(50), nullable=True)
    output_format = Column(String(50), nullable=True)
    language = Column(String(10), nullable=True)
    
    # Timestamps (UTC in DB, always assume UTC when reading)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.now(),
    )
    
    def __repr__(self) -> str:
        """Debug representation (NO preference values to prevent log leakage)."""
        return (
            f"UserPreference("
            f"id={self.preference_id[:8]}..., "
            f"user={self.user_id}, "
            f"created={self.created_at.isoformat() if self.created_at else None})"
        )

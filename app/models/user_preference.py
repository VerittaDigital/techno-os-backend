"""User preferences model for V-COF memory dignification."""

from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from uuid import uuid4

from app.models.session import Base


class UserPreferenceModel(Base):
    """User preferences persistence (F9.9-A).
    
    Stores explicit user preferences:
    - tone_preference: institutional|technical|conversational
    - output_format: text|bullet_points|checklist|table|structured
    - language: pt-BR|en-US
    
    Governance:
    - One preference record per user_id (UNIQUE constraint)
    - No psychological inference (explicit only)
    - LGPD compliance (deletable via DELETE endpoint)
    - Anti-enumeration (user_id validated against X-VERITTA-USER-ID header)
    """
    
    __tablename__ = "user_preferences"

    preference_id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
        comment="UUID primary key (Python-generated)"
    )
    user_id = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="User identifier (from X-VERITTA-USER-ID header)"
    )
    tone_preference = Column(
        String(50),
        nullable=True,
        comment="Tone: institutional|technical|conversational"
    )
    output_format = Column(
        String(50),
        nullable=True,
        comment="Format: text|bullet_points|checklist|table|structured"
    )
    language = Column(
        String(10),
        nullable=True,
        default='pt-BR',
        comment="Language: pt-BR|en-US"
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Creation timestamp (UTC)"
    )
    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
        comment="Last update timestamp (UTC)"
    )

    def to_dict(self):
        """Convert model to dict (for JSON serialization)."""
        return {
            "preference_id": self.preference_id,
            "user_id": self.user_id,
            "tone_preference": self.tone_preference,
            "output_format": self.output_format,
            "language": self.language,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

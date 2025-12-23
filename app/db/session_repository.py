"""Session repository for database CRUD operations."""

from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.session import SessionModel


class SessionRepository:
    """CRUD operations for sessions with fail-closed semantics."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(
        self,
        user_id: str,
        api_key_hash: str,
        ttl_hours: int = 8,
    ) -> SessionModel:
        """
        Create a new session.
        
        Args:
            user_id: User identifier
            api_key_hash: SHA256 hash of API key
            ttl_hours: Time-to-live in hours (default 8h)
        
        Returns:
            SessionModel with session_id populated
        
        Raises:
            IntegrityError: If creation fails
        """
        # Store as naive UTC (same as model)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        expires_at = now + timedelta(hours=ttl_hours)
        
        session = SessionModel(
            user_id=user_id,
            api_key_hash=api_key_hash,
            created_at=now,
            expires_at=expires_at,
            updated_at=now,
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        return session
    
    def get_by_id(self, session_id: str) -> Optional[SessionModel]:
        """
        Get session by ID.
        
        Fails-closed: Returns None if not found (no exception).
        """
        return self.db.query(SessionModel).filter(
            SessionModel.session_id == session_id
        ).first()
    
    def get_by_user_and_key(
        self,
        user_id: str,
        api_key_hash: str,
    ) -> list[SessionModel]:
        """
        Get all sessions for a user + api_key combination.
        
        Used for validation in F2.3 gate.
        """
        return self.db.query(SessionModel).filter(
            SessionModel.user_id == user_id,
            SessionModel.api_key_hash == api_key_hash,
        ).all()
    
    def revoke(self, session_id: str) -> Optional[SessionModel]:
        """
        Revoke a session by setting revoked_at.
        
        Revocation has priority over expiration.
        """
        session = self.get_by_id(session_id)
        if not session:
            return None
        
        # Store as naive UTC (same as model)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        session.revoked_at = now
        session.updated_at = now
        
        self.db.commit()
        self.db.refresh(session)
        
        return session
    
    def validate(self, session_id: str) -> tuple[bool, Optional[str]]:
        """
        Validate a session for F2.3 gate.
        
        Returns:
            (is_valid, reason_code)
            
        Reason codes:
            - SESSION_INVALID: Session not found
            - SESSION_REVOKED: Session revoked
            - SESSION_EXPIRED: Session expired
            - None: Session is valid
        """
        session = self.get_by_id(session_id)
        
        if not session:
            return False, "SESSION_INVALID"
        
        if session.is_revoked():
            return False, "SESSION_REVOKED"
        
        if session.is_expired():
            return False, "SESSION_EXPIRED"
        
        return True, None
    
    def cleanup_expired(self) -> int:
        """
        Delete all expired, non-revoked sessions.
        
        Returns:
            Number of sessions deleted
        """
        # Store as naive UTC (same as model)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        
        result = self.db.query(SessionModel).filter(
            SessionModel.expires_at <= now,
            SessionModel.revoked_at.is_(None),
        ).delete()
        
        self.db.commit()
        
        return result
    
    def get_active_count(self) -> int:
        """Get count of active (valid) sessions."""
        # Store as naive UTC (same as model)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        
        return self.db.query(SessionModel).filter(
            SessionModel.expires_at > now,
            SessionModel.revoked_at.is_(None),
        ).count()
    
    def get_by_user(self, user_id: str) -> list[SessionModel]:
        """Get all sessions for a user (including expired/revoked)."""
        return self.db.query(SessionModel).filter(
            SessionModel.user_id == user_id,
        ).all()

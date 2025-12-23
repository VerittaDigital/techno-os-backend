"""In-memory session store for F2.3 (beta).

SessionRecord: holds user_id, api_key_sha256 (binding), timestamps, revoked flag.
TTL: absolute 4 hours (no sliding window).
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
import hashlib


@dataclass
class SessionRecord:
    """Session record with TTL and binding info."""
    user_id: str
    api_key_sha256: str  # sha256(api_key), never the key itself
    created_at: datetime
    expires_at: datetime
    revoked: bool = False
    
    def is_valid(self) -> bool:
        """Check if session is not expired and not revoked."""
        now = datetime.now(timezone.utc)
        return not self.revoked and self.expires_at > now
    
    def is_expired(self) -> bool:
        """Check if session is expired (ignores revoked flag)."""
        now = datetime.now(timezone.utc)
        return self.expires_at <= now


def sha256_str(s: str) -> str:
    """SHA256 hash of string."""
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


class SessionStore:
    """In-memory session store (beta; not persistent)."""
    
    def __init__(self):
        self._store: Dict[str, SessionRecord] = {}
    
    def get(self, session_id: str) -> Optional[SessionRecord]:
        """Get session record; returns None if not found."""
        return self._store.get(session_id)
    
    def put(self, session_id: str, record: SessionRecord) -> None:
        """Store session record."""
        self._store[session_id] = record
    
    def delete(self, session_id: str) -> None:
        """Delete session record."""
        if session_id in self._store:
            del self._store[session_id]
    
    def revoke(self, session_id: str) -> None:
        """Mark session as revoked (soft delete)."""
        record = self.get(session_id)
        if record:
            record.revoked = True
    
    def clear_all(self) -> None:
        """Clear all sessions (for testing)."""
        self._store.clear()


# Global instance (singleton)
_session_store = SessionStore()


def get_session_store() -> SessionStore:
    """Get global session store instance."""
    return _session_store


def seed_session(
    session_id: str,
    user_id: str,
    api_key: str,
    created_at: Optional[datetime] = None,
    expires_at: Optional[datetime] = None,
) -> SessionRecord:
    """Seed a session (for testing)."""
    if created_at is None:
        created_at = datetime.now(timezone.utc)
    if expires_at is None:
        expires_at = created_at + timedelta(hours=4)
    
    api_key_sha256 = sha256_str(api_key)
    record = SessionRecord(
        user_id=user_id,
        api_key_sha256=api_key_sha256,
        created_at=created_at,
        expires_at=expires_at,
        revoked=False,
    )
    _session_store.put(session_id, record)
    return record

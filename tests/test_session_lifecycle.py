"""Tests for session lifecycle (TASK A1)."""

import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.models.session import SessionModel
from app.db.session_repository import SessionRepository


@pytest.fixture
def test_db():
    """Create in-memory SQLite for tests."""
    from sqlalchemy import event
    from sqlalchemy.pool import StaticPool
    
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Enable timezone support for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    SessionModel.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    yield db
    
    db.close()
    engine.dispose()


class TestSessionCreation:
    """Test session creation."""
    
    def test_create_valid_session(self, test_db: Session):
        """Test creating a new session."""
        repo = SessionRepository(test_db)
        
        session = repo.create(
            user_id="user_123",
            api_key_hash="abc123def456",
            ttl_hours=8,
        )
        
        assert session.session_id is not None
        assert session.user_id == "user_123"
        assert session.api_key_hash == "abc123def456"
        assert session.revoked_at is None
        assert session.is_valid()
    
    def test_session_has_uuid_format(self, test_db: Session):
        """Test session_id is UUID format."""
        repo = SessionRepository(test_db)
        
        session = repo.create(
            user_id="user_123",
            api_key_hash="abc123",
        )
        
        # UUID v4 = 36 chars (including hyphens)
        assert len(session.session_id) == 36
        assert session.session_id.count("-") == 4


class TestSessionValidation:
    """Test session validation logic."""
    
    def test_valid_session_passes_validation(self, test_db: Session):
        """Test valid session returns True."""
        repo = SessionRepository(test_db)
        
        session = repo.create(
            user_id="user_123",
            api_key_hash="abc123",
            ttl_hours=8,
        )
        
        is_valid, reason = repo.validate(session.session_id)
        
        assert is_valid is True
        assert reason is None
    
    def test_nonexistent_session(self, test_db: Session):
        """Test nonexistent session returns SESSION_INVALID."""
        repo = SessionRepository(test_db)
        
        is_valid, reason = repo.validate("nonexistent-uuid-here")
        
        assert is_valid is False
        assert reason == "SESSION_INVALID"
    
    def test_expired_session(self, test_db: Session):
        """Test expired session returns SESSION_EXPIRED."""
        repo = SessionRepository(test_db)
        
        # Create session with -1 hour TTL (already expired)
        now = datetime.now(timezone.utc)
        session = SessionModel(
            user_id="user_123",
            api_key_hash="abc123",
            created_at=now,
            expires_at=now - timedelta(hours=1),
            updated_at=now,
        )
        test_db.add(session)
        test_db.commit()
        
        is_valid, reason = repo.validate(session.session_id)
        
        assert is_valid is False
        assert reason == "SESSION_EXPIRED"
    
    def test_revoked_session(self, test_db: Session):
        """Test revoked session returns SESSION_REVOKED."""
        repo = SessionRepository(test_db)
        
        session = repo.create(
            user_id="user_123",
            api_key_hash="abc123",
            ttl_hours=8,
        )
        
        # Revoke it
        repo.revoke(session.session_id)
        
        is_valid, reason = repo.validate(session.session_id)
        
        assert is_valid is False
        assert reason == "SESSION_REVOKED"


class TestSessionRevocation:
    """Test session revocation."""
    
    def test_revoke_sets_revoked_at(self, test_db: Session):
        """Test revocation sets revoked_at timestamp."""
        repo = SessionRepository(test_db)
        
        session = repo.create(
            user_id="user_123",
            api_key_hash="abc123",
            ttl_hours=8,
        )
        
        revoked = repo.revoke(session.session_id)
        
        assert revoked.revoked_at is not None
        assert revoked.is_revoked()
    
    def test_revoke_nonexistent_session(self, test_db: Session):
        """Test revoking nonexistent session returns None."""
        repo = SessionRepository(test_db)
        
        result = repo.revoke("nonexistent-uuid")
        
        assert result is None
    
    def test_revocation_has_priority_over_expiration(self, test_db: Session):
        """Test revoked sessions are checked before expiration."""
        repo = SessionRepository(test_db)
        
        # Create already-expired session
        now = datetime.now(timezone.utc)
        session = SessionModel(
            user_id="user_123",
            api_key_hash="abc123",
            created_at=now,
            expires_at=now - timedelta(hours=1),
            updated_at=now,
        )
        test_db.add(session)
        test_db.commit()
        
        # Revoke it
        repo.revoke(session.session_id)
        
        is_valid, reason = repo.validate(session.session_id)
        
        # Should return REVOKED, not EXPIRED
        assert reason == "SESSION_REVOKED"


class TestSessionConcurrency:
    """Test concurrent session access."""
    
    def test_concurrent_validation(self, test_db: Session):
        """Test multiple validations don't interfere."""
        repo = SessionRepository(test_db)
        
        # Create multiple sessions
        sessions = [
            repo.create(f"user_{i}", f"key_{i}", ttl_hours=8)
            for i in range(5)
        ]
        
        # Validate all
        for session in sessions:
            is_valid, reason = repo.validate(session.session_id)
            assert is_valid is True
            assert reason is None
    
    def test_concurrent_revoke(self, test_db: Session):
        """Test revoking one session doesn't affect others."""
        repo = SessionRepository(test_db)
        
        session1 = repo.create("user_1", "key_1", ttl_hours=8)
        session2 = repo.create("user_2", "key_2", ttl_hours=8)
        
        # Revoke session1
        repo.revoke(session1.session_id)
        
        # session1 should be revoked
        is_valid, reason = repo.validate(session1.session_id)
        assert is_valid is False
        assert reason == "SESSION_REVOKED"
        
        # session2 should still be valid
        is_valid, reason = repo.validate(session2.session_id)
        assert is_valid is True
        assert reason is None


class TestSessionBoundary:
    """Test TTL boundary conditions."""
    
    def test_session_expires_at_exact_time(self, test_db: Session):
        """Test session expiration at exact timestamp."""
        repo = SessionRepository(test_db)
        
        # Create session with TTL = 1 second
        session = repo.create(
            user_id="user_123",
            api_key_hash="abc123",
            ttl_hours=0,  # Will set expires_at ~now
        )
        
        # Adjust expires_at to 1 second in future
        now = datetime.now(timezone.utc)
        session.expires_at = now + timedelta(seconds=1)
        test_db.commit()
        
        # Should be valid now
        is_valid, reason = repo.validate(session.session_id)
        assert is_valid is True
        
        # After 1 second, should be expired
        session.expires_at = now
        test_db.commit()
        
        is_valid, reason = repo.validate(session.session_id)
        assert is_valid is False
        assert reason == "SESSION_EXPIRED"


class TestSessionCleanup:
    """Test expired session cleanup."""
    
    def test_cleanup_expired_sessions(self, test_db: Session):
        """Test cleanup removes expired but not revoked sessions."""
        repo = SessionRepository(test_db)
        
        now = datetime.now(timezone.utc)
        
        # Create expired session
        expired = SessionModel(
            user_id="user_1",
            api_key_hash="key_1",
            created_at=now,
            expires_at=now - timedelta(hours=1),
            updated_at=now,
        )
        test_db.add(expired)
        
        # Create revoked session (should not be deleted)
        revoked = SessionModel(
            user_id="user_2",
            api_key_hash="key_2",
            created_at=now,
            expires_at=now - timedelta(hours=1),
            revoked_at=now,
            updated_at=now,
        )
        test_db.add(revoked)
        
        # Create valid session
        valid = repo.create("user_3", "key_3", ttl_hours=8)
        
        test_db.commit()
        
        # Run cleanup
        deleted_count = repo.cleanup_expired()
        
        # Should delete only expired (not revoked)
        assert deleted_count == 1
        
        # Verify valid session still exists
        is_valid, _ = repo.validate(valid.session_id)
        assert is_valid is True

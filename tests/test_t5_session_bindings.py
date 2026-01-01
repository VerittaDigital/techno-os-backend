"""Tests for SessionStore and UserBindings (T5)."""

from datetime import datetime, timedelta, timezone
from app.session_store import (
    SessionRecord,
    SessionStore,
    sha256_str,
    seed_session,
    get_session_store,
)
from app.f23_bindings import UserBindings


class TestSessionRecord:
    """Test SessionRecord validation."""
    
    def test_is_valid_within_ttl(self):
        """Session is valid within TTL window."""
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=1)
        record = SessionRecord(
            user_id="u_12345678",
            api_key_sha256="abc123",
            created_at=now,
            expires_at=expires_at,
            revoked=False,
        )
        assert record.is_valid() is True
    
    def test_is_expired_after_ttl(self):
        """Session is invalid after TTL expires."""
        now = datetime.now(timezone.utc)
        expires_at = now - timedelta(hours=1)  # already expired
        record = SessionRecord(
            user_id="u_12345678",
            api_key_sha256="abc123",
            created_at=now - timedelta(hours=2),
            expires_at=expires_at,
            revoked=False,
        )
        assert record.is_valid() is False
        assert record.is_expired() is True
    
    def test_is_invalid_when_revoked(self):
        """Session is invalid if revoked flag is set."""
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=1)  # not expired
        record = SessionRecord(
            user_id="u_12345678",
            api_key_sha256="abc123",
            created_at=now,
            expires_at=expires_at,
            revoked=True,
        )
        assert record.is_valid() is False
        assert record.is_expired() is False


class TestSha256:
    """Test SHA256 hashing."""
    
    def test_sha256_str_consistent(self):
        """SHA256 hash is consistent."""
        api_key = "sk_test_abc123"
        hash1 = sha256_str(api_key)
        hash2 = sha256_str(api_key)
        assert hash1 == hash2
    
    def test_sha256_str_length(self):
        """SHA256 hash is 64 chars (hex)."""
        api_key = "sk_test_abc123"
        hash_val = sha256_str(api_key)
        assert len(hash_val) == 64


class TestSessionStore:
    """Test SessionStore get/put/delete."""
    
    def test_put_get(self):
        """Store and retrieve session."""
        store = SessionStore()
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=4)
        record = SessionRecord(
            user_id="u_12345678",
            api_key_sha256="abc123",
            created_at=now,
            expires_at=expires_at,
        )
        store.put("sess_abc123", record)
        retrieved = store.get("sess_abc123")
        assert retrieved is not None
        assert retrieved.user_id == "u_12345678"
    
    def test_get_missing_returns_none(self):
        """Get missing session returns None."""
        store = SessionStore()
        assert store.get("sess_missing") is None
    
    def test_delete(self):
        """Delete session removes it."""
        store = SessionStore()
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=4)
        record = SessionRecord(
            user_id="u_12345678",
            api_key_sha256="abc123",
            created_at=now,
            expires_at=expires_at,
        )
        store.put("sess_abc123", record)
        assert store.get("sess_abc123") is not None
        store.delete("sess_abc123")
        assert store.get("sess_abc123") is None
    
    def test_revoke(self):
        """Revoke marks session as revoked."""
        store = SessionStore()
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=4)
        record = SessionRecord(
            user_id="u_12345678",
            api_key_sha256="abc123",
            created_at=now,
            expires_at=expires_at,
            revoked=False,
        )
        store.put("sess_abc123", record)
        store.revoke("sess_abc123")
        retrieved = store.get("sess_abc123")
        assert retrieved is not None
        assert retrieved.revoked is True
        assert retrieved.is_valid() is False


class TestSeedSession:
    """Test session seeding helper."""
    
    def test_seed_session_with_defaults(self):
        """Seed session with default TTL."""
        store = get_session_store()
        store.clear_all()
        
        record = seed_session(
            session_id="sess_test123",
            user_id="u_12345678",
            api_key="sk_test_abc123",
        )
        
        assert record.user_id == "u_12345678"
        assert record.api_key_sha256 == sha256_str("sk_test_abc123")
        assert record.revoked is False
        # Check TTL is approximately 4 hours
        ttl_seconds = (record.expires_at - record.created_at).total_seconds()
        assert 3600 * 4 - 5 <= ttl_seconds <= 3600 * 4 + 5  # within 5 seconds
    
    def test_seed_session_stored_in_global(self):
        """Seed session is stored in global session store."""
        store = get_session_store()
        store.clear_all()
        
        seed_session(
            session_id="sess_test456",
            user_id="u_87654321",
            api_key="sk_test_xyz789",
        )
        
        retrieved = store.get("sess_test456")
        assert retrieved is not None
        assert retrieved.user_id == "u_87654321"


class TestUserBindings:
    """Test UserBindings get/add/remove."""
    
    def test_add_and_get_binding(self):
        """Add and retrieve user binding."""
        bindings = UserBindings()
        api_key_sha256 = sha256_str("sk_test_abc")
        
        bindings.add_binding(api_key_sha256, "u_user1")
        allowed = bindings.get_allowed_user_ids(api_key_sha256)
        
        assert "u_user1" in allowed
    
    def test_get_nonexistent_binding_returns_empty_set(self):
        """Get nonexistent api_key returns empty set (fail-closed)."""
        bindings = UserBindings()
        allowed = bindings.get_allowed_user_ids("nonexistent_hash")
        assert allowed == set()
    
    def test_add_multiple_users_to_same_key(self):
        """Add multiple users to same api_key."""
        bindings = UserBindings()
        api_key_sha256 = sha256_str("sk_test_abc")
        
        bindings.add_binding(api_key_sha256, "u_user1")
        bindings.add_binding(api_key_sha256, "u_user2")
        allowed = bindings.get_allowed_user_ids(api_key_sha256)
        
        assert len(allowed) == 2
        assert "u_user1" in allowed
        assert "u_user2" in allowed
    
    def test_remove_binding(self):
        """Remove user from binding."""
        bindings = UserBindings()
        api_key_sha256 = sha256_str("sk_test_abc")
        
        bindings.add_binding(api_key_sha256, "u_user1")
        bindings.add_binding(api_key_sha256, "u_user2")
        bindings.remove_binding(api_key_sha256, "u_user1")
        allowed = bindings.get_allowed_user_ids(api_key_sha256)
        
        assert "u_user1" not in allowed
        assert "u_user2" in allowed

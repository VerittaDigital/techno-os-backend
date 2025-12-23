"""Pytest configuration and fixtures."""
import os
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.action_matrix import reset_action_matrix


# ============================================================================
# Session Setup: Configure test environment
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def configure_test_environment():
    """Configure standard environment variables for all tests.
    
    Ensures:
    - VERITTA_BETA_API_KEY is always set (prevents 500 on missing auth)
    - VERITTA_PROFILES_FINGERPRINT is set (P1.1 invariant)
    - DATABASE_URL uses in-memory SQLite (isolation)
    - VERITTA_ADMIN_API_KEY is set (for admin tests)
    
    This prevents failures due to missing environment configuration.
    """
    os.environ["VERITTA_BETA_API_KEY"] = "TEST_BETA_API_KEY_VALID_FOR_TESTING"
    os.environ["VERITTA_PROFILES_FINGERPRINT"] = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["VERITTA_ADMIN_API_KEY"] = "TEST_ADMIN_API_KEY_VALID_FOR_TESTING"
    os.environ["VERITTA_SESSION_TTL_HOURS"] = "8"
    os.environ["VERITTA_AUDIT_LOG_PATH"] = "./audit_test.log"
    os.environ["LOG_LEVEL"] = "INFO"


# ============================================================================
# Database Setup
# ============================================================================

@pytest.fixture
def test_db_engine():
    """Create an in-memory SQLite engine for tests."""
    engine = create_engine("sqlite:///:memory:")
    
    # Initialize schema
    from app.models.session import Base
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Cleanup
    engine.dispose()


@pytest.fixture
def test_db_session(test_db_engine):
    """Create a new database session for a test with transaction isolation."""
    connection = test_db_engine.connect()
    transaction = connection.begin()
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = SessionLocal()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


# ============================================================================
# Test Client Setup
# ============================================================================

@pytest.fixture
def test_client(test_db_session):
    """FastAPI TestClient with database isolation.
    
    This ensures:
    - Each test has isolated database
    - No data leakage between tests  
    - Dependency injection works correctly
    """
    from app.main import app
    from app.db.database import get_db
    
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass  # Fixture handles cleanup
    
    app.dependency_overrides[get_db] = override_get_db
    
    client = TestClient(app)
    
    # Add convenience method to send authenticated requests with X-API-Key header
    def authenticated_request(method, path, **kwargs):
        """Send request with X-API-Key header (F2.1 auth mode).
        
        Usage:
            response = client.authenticated_request('POST', '/process', json={"text": "hello"})
        """
        headers = kwargs.pop('headers', {})
        headers['X-API-Key'] = os.environ.get("VERITTA_BETA_API_KEY", "TEST_BETA_API_KEY_VALID_FOR_TESTING")
        
        method_lower = method.lower()
        if method_lower == 'get':
            return client.get(path, headers=headers, **kwargs)
        elif method_lower == 'post':
            return client.post(path, headers=headers, **kwargs)
        elif method_lower == 'put':
            return client.put(path, headers=headers, **kwargs)
        elif method_lower == 'delete':
            return client.delete(path, headers=headers, **kwargs)
        elif method_lower == 'patch':
            return client.patch(path, headers=headers, **kwargs)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
    
    client.authenticated_request = authenticated_request
    
    yield client
    
    # Cleanup
    if get_db in app.dependency_overrides:
        del app.dependency_overrides[get_db]


# Alias for backward compatibility with tests that request 'client' instead of 'test_client'
@pytest.fixture
def client(test_client):
    """Alias for test_client fixture."""
    return test_client


# ============================================================================
# Cleanup & Reset Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_audit_log():
    """Cleanup audit log before and after each test.
    
    Prevents:
    - Audit log contamination between tests
    - Tests reading stale entries
    """
    audit_log_path = os.getenv("VERITTA_AUDIT_LOG_PATH", "./audit_test.log")
    
    # Remove if exists before test
    if Path(audit_log_path).exists():
        try:
            Path(audit_log_path).unlink()
        except OSError:
            pass
    
    yield
    
    # Cleanup after test
    if Path(audit_log_path).exists():
        try:
            Path(audit_log_path).unlink()
        except OSError:
            pass


@pytest.fixture(autouse=True)
def reset_action_matrix_after_test():
    """Reset action matrix after each test."""
    yield
    reset_action_matrix()


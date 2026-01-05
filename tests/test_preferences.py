"""Unit and integration tests for user preferences API (F9.9-A).

Tests cover:
- Model validation
- Schema validation (enums, fail-closed)
- Auth dependency (user_id extraction)
- GET endpoint (existing/non-existing preferences)
- PUT endpoint (create/update, partial update)
- Security (user_id in payload rejected)
- Privacy (no logging of values)

Coverage target: >=80% for preferences module.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from fastapi import HTTPException, Request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4

from app.models.user_preference import UserPreference, Base
from app.schemas.preferences import (
    ToneEnum,
    OutputFormatEnum,
    LanguageEnum,
    PreferencesPutRequest,
    PreferencesGetResponse,
)
from app.dependencies.auth import get_user_from_gate


# Test database setup (unique per test session)
def get_test_db_url():
    """Generate unique test DB URL."""
    return f"sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_engine():
    """Create test engine."""
    engine = create_engine(get_test_db_url(), connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db_session(test_engine):
    """Create test database session with fresh schema."""
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestSessionLocal()
    yield session
    session.close()


@pytest.fixture
def mock_request():
    """Mock FastAPI Request with auth headers."""
    request = Mock(spec=Request)
    request.headers = {"X-VERITTA-USER-ID": "u_12345678"}
    request.state = Mock(trace_id="test_trace_123")
    return request


@pytest.fixture
def mock_request_no_user():
    """Mock FastAPI Request without user_id header."""
    request = Mock(spec=Request)
    request.headers = {}
    request.state = Mock(trace_id="test_trace_123")
    return request


# ==============================================================================
# UNIT TESTS — Model
# ==============================================================================

def test_user_preference_model_creation(db_session):
    """Test UserPreference model can be created."""
    pref = UserPreference(
        preference_id=str(uuid4()),
        user_id="u_12345678",
        tone_preference="institucional",
        output_format="markdown",
        language="pt-BR",
    )
    db_session.add(pref)
    db_session.commit()
    
    assert pref.preference_id is not None
    assert pref.user_id == "u_12345678"
    assert pref.tone_preference == "institucional"


def test_user_preference_unique_user_id(db_session):
    """Test UNIQUE constraint on user_id."""
    pref1 = UserPreference(
        preference_id=str(uuid4()),
        user_id="u_12345678",
        tone_preference="institucional",
    )
    db_session.add(pref1)
    db_session.commit()
    
    # Attempt to insert duplicate user_id
    pref2 = UserPreference(
        preference_id=str(uuid4()),
        user_id="u_12345678",  # Same user_id
        tone_preference="tecnico",
    )
    db_session.add(pref2)
    
    with pytest.raises(Exception):  # SQLAlchemy IntegrityError
        db_session.commit()


def test_user_preference_repr_no_value_leak():
    """Test __repr__ does not leak preference values (privacy)."""
    pref = UserPreference(
        preference_id=str(uuid4()),
        user_id="u_12345678",
        tone_preference="institucional",
    )
    repr_str = repr(pref)
    
    # Should NOT contain preference values
    assert "institucional" not in repr_str
    assert "u_12345678" in repr_str  # user_id OK (not sensitive)


# ==============================================================================
# UNIT TESTS — Schemas
# ==============================================================================

def test_schema_tone_enum_valid():
    """Test ToneEnum accepts valid values."""
    assert ToneEnum.institucional.value == "institucional"
    assert ToneEnum.tecnico.value == "tecnico"
    assert ToneEnum.casual.value == "casual"


def test_schema_tone_enum_invalid():
    """Test ToneEnum rejects invalid values."""
    with pytest.raises(ValueError):
        ToneEnum("invalid_tone")


def test_schema_put_request_valid():
    """Test PreferencesPutRequest accepts valid data."""
    req = PreferencesPutRequest(
        tone=ToneEnum.institucional,
        output_format=OutputFormatEnum.markdown,
        language=LanguageEnum.pt_br,
    )
    assert req.tone == ToneEnum.institucional
    assert req.output_format == OutputFormatEnum.markdown
    assert req.language == LanguageEnum.pt_br


def test_schema_put_request_partial():
    """Test PreferencesPutRequest allows partial updates (all optional)."""
    req = PreferencesPutRequest(tone=ToneEnum.tecnico)
    assert req.tone == ToneEnum.tecnico
    assert req.output_format is None
    assert req.language is None


def test_schema_put_request_empty_string_to_none():
    """Test empty strings converted to None."""
    req = PreferencesPutRequest.model_validate({"tone": "", "output_format": "json"})
    assert req.tone is None
    assert req.output_format == OutputFormatEnum.json


# ==============================================================================
# UNIT TESTS — Auth Dependency
# ==============================================================================

async def test_get_user_from_gate_success(mock_request):
    """Test user_id extraction from header."""
    user_id = await get_user_from_gate(mock_request)
    assert user_id == "u_12345678"


async def test_get_user_from_gate_missing_header(mock_request_no_user):
    """Test fail-closed when user_id header missing."""
    with pytest.raises(HTTPException) as exc_info:
        await get_user_from_gate(mock_request_no_user)
    
    assert exc_info.value.status_code == 500
    assert "gate bypass" in str(exc_info.value.detail).lower()


# ==============================================================================
# INTEGRATION TESTS — GET Endpoint
# ==============================================================================

async def test_get_preferences_not_found(db_session, mock_request):
    """Test GET returns null values when preferences don't exist."""
    from app.routes.preferences import get_preferences
    
    response = await get_preferences(
        request=mock_request,
        user_id="u_12345678",
        db=db_session,
    )
    
    assert response.user_id == "u_12345678"
    assert response.tone is None
    assert response.output_format is None
    assert response.language is None


async def test_get_preferences_existing(db_session, mock_request):
    """Test GET returns existing preferences."""
    # Seed preferences
    pref = UserPreference(
        preference_id=str(uuid4()),
        user_id="u_12345678",
        tone_preference="institucional",
        output_format="markdown",
        language="pt-BR",
    )
    db_session.add(pref)
    db_session.commit()
    
    from app.routes.preferences import get_preferences
    
    response = await get_preferences(
        request=mock_request,
        user_id="u_12345678",
        db=db_session,
    )
    
    assert response.user_id == "u_12345678"
    assert response.tone == "institucional"
    assert response.output_format == "markdown"
    assert response.language == "pt-BR"


# ==============================================================================
# INTEGRATION TESTS — PUT Endpoint
# ==============================================================================

async def test_put_preferences_create(db_session, mock_request):
    """Test PUT creates new preferences."""
    from app.routes.preferences import put_preferences
    
    # Mock request.body() to return empty (no user_id in payload)
    mock_request.body = AsyncMock(return_value=b'{"tone":"institucional"}')
    
    body = PreferencesPutRequest(tone=ToneEnum.institucional)
    
    response = await put_preferences(
        request=mock_request,
        body=body,
        user_id="u_12345678",
        db=db_session,
    )
    
    assert response.user_id == "u_12345678"
    assert response.tone == "institucional"
    assert response.message == "Preferences updated successfully"
    
    # Verify in DB
    pref = db_session.query(UserPreference).filter(
        UserPreference.user_id == "u_12345678"
    ).first()
    assert pref is not None
    assert pref.tone_preference == "institucional"


async def test_put_preferences_update(db_session, mock_request):
    """Test PUT updates existing preferences."""
    # Seed existing preferences
    pref = UserPreference(
        preference_id=str(uuid4()),
        user_id="u_12345678",
        tone_preference="tecnico",
        output_format="json",
    )
    db_session.add(pref)
    db_session.commit()
    
    from app.routes.preferences import put_preferences
    
    mock_request.body = AsyncMock(return_value=b'{"tone":"institucional"}')
    body = PreferencesPutRequest(tone=ToneEnum.institucional)
    
    response = await put_preferences(
        request=mock_request,
        body=body,
        user_id="u_12345678",
        db=db_session,
    )
    
    assert response.tone == "institucional"
    assert response.output_format == "json"  # Unchanged


async def test_put_preferences_partial_update(db_session, mock_request):
    """Test PUT with partial update (only some fields)."""
    # Seed existing
    pref = UserPreference(
        preference_id=str(uuid4()),
        user_id="u_12345678",
        tone_preference="tecnico",
        output_format="json",
        language="en-US",
    )
    db_session.add(pref)
    db_session.commit()
    
    from app.routes.preferences import put_preferences
    
    # Update only language
    mock_request.body = AsyncMock(return_value=b'{"language":"pt-BR"}')
    body = PreferencesPutRequest(language=LanguageEnum.pt_br)
    
    response = await put_preferences(
        request=mock_request,
        body=body,
        user_id="u_12345678",
        db=db_session,
    )
    
    # language updated, others unchanged
    assert response.tone == "tecnico"
    assert response.output_format == "json"
    assert response.language == "pt-BR"


async def test_put_preferences_reject_user_id_in_payload(db_session, mock_request):
    """Test PUT rejects user_id in request body (fail-closed security)."""
    from app.routes.preferences import put_preferences
    
    # Malicious payload with user_id
    mock_request.body = AsyncMock(return_value=b'{"user_id":"u_hacked","tone":"institucional"}')
    body = PreferencesPutRequest(tone=ToneEnum.institucional)
    
    with pytest.raises(HTTPException) as exc_info:
        await put_preferences(
            request=mock_request,
            body=body,
            user_id="u_12345678",
            db=db_session,
        )
    
    assert exc_info.value.status_code == 400
    assert "user_id cannot be specified" in str(exc_info.value.detail).lower()


# ==============================================================================
# INTEGRATION TESTS — Invalid Enums (Fail-Closed)
# ==============================================================================

def test_put_preferences_invalid_tone():
    """Test invalid tone value rejected by Pydantic."""
    with pytest.raises(ValueError):
        PreferencesPutRequest.model_validate({"tone": "invalid_tone"})


def test_put_preferences_invalid_format():
    """Test invalid output_format rejected by Pydantic."""
    with pytest.raises(ValueError):
        PreferencesPutRequest.model_validate({"output_format": "invalid_format"})


def test_put_preferences_invalid_language():
    """Test invalid language rejected by Pydantic."""
    with pytest.raises(ValueError):
        PreferencesPutRequest.model_validate({"language": "invalid_lang"})

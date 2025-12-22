"""
Tests for trace_id validation in contracts (DecisionRecord, ActionRequest, ActionResult).

Verifies that trace_id must be:
1. Non-empty (not empty string, not whitespace)
2. Valid UUID format
"""

import uuid
import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from app.decision_record import DecisionRecord
from app.action_contracts import ActionRequest, ActionResult


class TestDecisionRecordTraceIdValidation:
    """Test suite for DecisionRecord.trace_id validation."""

    def test_decision_record_rejects_empty_trace_id(self):
        """DecisionRecord with empty trace_id must raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            DecisionRecord(
                decision="ALLOW",
                profile_id="default",
                profile_hash="abc123",
                matched_rules=[],
                reason_codes=[],
                input_digest="def456",
                trace_id="",  # Empty string
                ts_utc=datetime.now(timezone.utc),
            )
        
        # Verify error message mentions trace_id
        assert "trace_id" in str(exc_info.value).lower()

    def test_decision_record_rejects_whitespace_trace_id(self):
        """DecisionRecord with whitespace-only trace_id must raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            DecisionRecord(
                decision="DENY",
                profile_id="default",
                profile_hash="abc123",
                matched_rules=[],
                reason_codes=["UNKNOWN_FIELD"],
                input_digest="def456",
                trace_id="   ",  # Whitespace only
                ts_utc=datetime.now(timezone.utc),
            )
        
        assert "trace_id" in str(exc_info.value).lower()

    def test_decision_record_rejects_non_uuid_trace_id(self):
        """DecisionRecord with non-UUID trace_id must raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            DecisionRecord(
                decision="ALLOW",
                profile_id="default",
                profile_hash="abc123",
                matched_rules=[],
                reason_codes=[],
                input_digest="def456",
                trace_id="not-a-uuid",  # Invalid UUID
                ts_utc=datetime.now(timezone.utc),
            )
        
        error_str = str(exc_info.value).lower()
        assert "trace_id" in error_str
        assert "uuid" in error_str

    def test_decision_record_accepts_valid_uuid_trace_id(self):
        """DecisionRecord with valid UUID trace_id must pass validation."""
        valid_trace_id = str(uuid.uuid4())
        
        record = DecisionRecord(
            decision="ALLOW",
            profile_id="default",
            profile_hash="abc123",
            matched_rules=["rule1"],
            reason_codes=[],
            input_digest="def456",
            trace_id=valid_trace_id,
            ts_utc=datetime.now(timezone.utc),
        )
        
        assert record.trace_id == valid_trace_id


class TestActionRequestTraceIdValidation:
    """Test suite for ActionRequest.trace_id validation."""

    def test_action_request_rejects_empty_trace_id(self):
        """ActionRequest with empty trace_id must raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ActionRequest(
                action="process",
                payload={"text": "hello"},
                trace_id="",  # Empty string
                ts_utc=datetime.now(timezone.utc),
            )
        
        assert "trace_id" in str(exc_info.value).lower()

    def test_action_request_rejects_whitespace_trace_id(self):
        """ActionRequest with whitespace-only trace_id must raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ActionRequest(
                action="process",
                payload={"text": "hello"},
                trace_id="  \t  ",  # Whitespace with tab
                ts_utc=datetime.now(timezone.utc),
            )
        
        assert "trace_id" in str(exc_info.value).lower()

    def test_action_request_rejects_non_uuid_trace_id(self):
        """ActionRequest with non-UUID trace_id must raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ActionRequest(
                action="process",
                payload={"text": "hello"},
                trace_id="not-a-uuid-123",  # Invalid UUID
                ts_utc=datetime.now(timezone.utc),
            )
        
        error_str = str(exc_info.value).lower()
        assert "trace_id" in error_str
        assert "uuid" in error_str

    def test_action_request_accepts_valid_uuid_trace_id(self):
        """ActionRequest with valid UUID trace_id must pass validation."""
        valid_trace_id = str(uuid.uuid4())
        
        request = ActionRequest(
            action="process",
            payload={"text": "hello"},
            trace_id=valid_trace_id,
            ts_utc=datetime.now(timezone.utc),
        )
        
        assert request.trace_id == valid_trace_id


class TestActionResultTraceIdValidation:
    """Test suite for ActionResult.trace_id validation."""

    def test_action_result_rejects_empty_trace_id(self):
        """ActionResult with empty trace_id must raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ActionResult(
                action="process",
                executor_id="text_process_v1",
                executor_version="1.0.0",
                status="SUCCESS",
                reason_codes=[],
                input_digest="abc123",
                output_digest="def456",
                trace_id="",  # Empty string
                ts_utc=datetime.now(timezone.utc),
            )
        
        assert "trace_id" in str(exc_info.value).lower()

    def test_action_result_rejects_whitespace_trace_id(self):
        """ActionResult with whitespace-only trace_id must raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ActionResult(
                action="process",
                executor_id="text_process_v1",
                executor_version="1.0.0",
                status="FAILED",
                reason_codes=["EXECUTOR_EXCEPTION"],
                input_digest="abc123",
                output_digest=None,
                trace_id="    ",  # Whitespace only
                ts_utc=datetime.now(timezone.utc),
            )
        
        assert "trace_id" in str(exc_info.value).lower()

    def test_action_result_rejects_non_uuid_trace_id(self):
        """ActionResult with non-UUID trace_id must raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ActionResult(
                action="process",
                executor_id="text_process_v1",
                executor_version="1.0.0",
                status="BLOCKED",
                reason_codes=["EXECUTOR_TIMEOUT"],
                input_digest="abc123",
                output_digest=None,
                trace_id="invalid-uuid-format",  # Invalid UUID
                ts_utc=datetime.now(timezone.utc),
            )
        
        error_str = str(exc_info.value).lower()
        assert "trace_id" in error_str
        assert "uuid" in error_str

    def test_action_result_accepts_valid_uuid_trace_id(self):
        """ActionResult with valid UUID trace_id must pass validation."""
        valid_trace_id = str(uuid.uuid4())
        
        result = ActionResult(
            action="process",
            executor_id="text_process_v1",
            executor_version="1.0.0",
            status="SUCCESS",
            reason_codes=[],
            input_digest="abc123",
            output_digest="def456",
            trace_id=valid_trace_id,
            ts_utc=datetime.now(timezone.utc),
        )
        
        assert result.trace_id == valid_trace_id

"""Tests for DecisionRecord and input digest."""
from datetime import datetime, timezone
import pytest

from app.decision_record import DecisionRecord, make_input_digest


class TestDecisionRecord:
    """DecisionRecord fields and timezone semantics."""

    def test_fields_exist(self):
        """DecisionRecord has all required fields."""
        record = DecisionRecord(
            decision="ALLOW",
            profile_id="test_profile",
            profile_hash="abc123",
            matched_rules=["rule1"],
            reason_codes=["OK"],
            input_digest="deadbeef",
            trace_id="trace-001",
            ts_utc=datetime.now(timezone.utc),
        )
        assert record.decision == "ALLOW"
        assert record.profile_id == "test_profile"
        assert record.profile_hash == "abc123"
        assert record.matched_rules == ["rule1"]
        assert record.reason_codes == ["OK"]
        assert record.input_digest == "deadbeef"
        assert record.trace_id == "trace-001"

    def test_ts_utc_must_be_timezone_aware(self):
        """ts_utc must be UTC-aware datetime."""
        with pytest.raises(ValueError, match="timezone-aware"):
            DecisionRecord(
                decision="DENY",
                profile_id="test",
                profile_hash="",
                matched_rules=[],
                reason_codes=["GATE_EXCEPTION"],
                input_digest="x",
                trace_id="trace-001",
                ts_utc=datetime.now(),  # naive datetime
            )

    def test_ts_utc_must_be_utc(self):
        """ts_utc must be in UTC, not other timezones."""
        from datetime import timedelta, tzinfo

        # Create a timezone that's UTC+1
        class UTC_Plus_1(tzinfo):
            def utcoffset(self, dt):
                return timedelta(hours=1)
            def tzname(self, dt):
                return "UTC+1"
            def dst(self, dt):
                return timedelta(0)

        with pytest.raises(ValueError, match="UTC"):
            DecisionRecord(
                decision="DENY",
                profile_id="test",
                profile_hash="",
                matched_rules=[],
                reason_codes=["GATE_EXCEPTION"],
                input_digest="x",
                trace_id="trace-001",
                ts_utc=datetime.now(UTC_Plus_1()),
            )

    def test_default_ts_utc_is_now_utc(self):
        """If ts_utc is not provided, defaults to now in UTC."""
        before = datetime.now(timezone.utc)
        record = DecisionRecord(
            decision="ALLOW",
            profile_id="test",
            profile_hash="",
            matched_rules=[],
            reason_codes=["OK"],
            input_digest="x",
            trace_id="trace-001",
        )
        after = datetime.now(timezone.utc)

        assert before <= record.ts_utc <= after
        assert record.ts_utc.tzinfo == timezone.utc


class TestInputDigest:
    """make_input_digest determinism and correctness."""

    def test_digest_stable_across_key_order(self):
        """Digest is identical regardless of dict key insertion order."""
        payload_1 = {"b": 2, "a": 1}
        payload_2 = {"a": 1, "b": 2}

        digest_1 = make_input_digest(payload_1)
        digest_2 = make_input_digest(payload_2)

        assert digest_1 == digest_2
        # Ensure it's a valid sha256 hex
        assert len(digest_1) == 64
        assert all(c in "0123456789abcdef" for c in digest_1)

    def test_digest_stable_across_nested_keys(self):
        """Digest is stable for nested structures with reordered keys."""
        payload_1 = {"z": {"y": 2, "x": 1}, "a": 1}
        payload_2 = {"a": 1, "z": {"x": 1, "y": 2}}

        digest_1 = make_input_digest(payload_1)
        digest_2 = make_input_digest(payload_2)

        assert digest_1 == digest_2

    def test_digest_empty_dict(self):
        """Empty dict produces valid digest."""
        digest = make_input_digest({})
        assert len(digest) == 64
        assert all(c in "0123456789abcdef" for c in digest)

    def test_digest_empty_list(self):
        """Empty list produces valid digest."""
        digest = make_input_digest([])
        assert len(digest) == 64

    def test_digest_unicode_preserved(self):
        """Unicode characters are preserved (ensure_ascii=False)."""
        payload = {"text": "こんにちは"}  # "hello" in Japanese
        digest_1 = make_input_digest(payload)

        # Change unicode content, digest must differ
        payload_2 = {"text": "さようなら"}  # "goodbye" in Japanese
        digest_2 = make_input_digest(payload_2)

        assert digest_1 != digest_2

    def test_digest_non_json_serializable_fallback(self):
        """Non-JSON-serializable objects fall back to str() representation."""
        class CustomObj:
            def __str__(self):
                return "custom_repr"

        obj = CustomObj()
        digest = make_input_digest(obj)

        # P1.4: Non-JSON-serializable objects return None (privacy-first, no str() fallback)
        assert digest is None

    def test_digest_different_payloads_differ(self):
        """Different payloads produce different digests."""
        digest_1 = make_input_digest({"a": 1})
        digest_2 = make_input_digest({"a": 2})

        assert digest_1 != digest_2

    def test_digest_list_order_matters(self):
        """List order affects digest (lists are ordered)."""
        digest_1 = make_input_digest([1, 2, 3])
        digest_2 = make_input_digest([3, 2, 1])

        assert digest_1 != digest_2


class TestDecisionRecordDenyValidator:
    """Test that DENY decision requires reason_codes."""

    def test_deny_without_reason_codes_raises_error(self):
        """DENY decision with empty reason_codes must raise ValidationError."""
        with pytest.raises(ValueError, match="reason_codes must be non-empty when decision is DENY"):
            DecisionRecord(
                decision="DENY",
                profile_id="test",
                profile_hash="",
                matched_rules=[],
                reason_codes=[],  # Empty list should fail
                input_digest="x",
                trace_id="trace-001",
                ts_utc=datetime.now(timezone.utc),
            )

    def test_deny_with_valid_reason_codes_passes(self):
        """DENY decision with non-empty reason_codes must pass."""
        record = DecisionRecord(
            decision="DENY",
            profile_id="test",
            profile_hash="",
            matched_rules=[],
            reason_codes=["GATE_EXCEPTION"],  # Non-empty list should pass
            input_digest="x",
            trace_id="trace-001",
            ts_utc=datetime.now(timezone.utc),
        )
        assert record.decision == "DENY"
        assert record.reason_codes == ["GATE_EXCEPTION"]

    def test_allow_with_empty_reason_codes_passes(self):
        """ALLOW decision can have empty reason_codes."""
        record = DecisionRecord(
            decision="ALLOW",
            profile_id="test",
            profile_hash="",
            matched_rules=[],
            reason_codes=[],  # Empty is OK for ALLOW
            input_digest="x",
            trace_id="trace-001",
            ts_utc=datetime.now(timezone.utc),
        )
        assert record.decision == "ALLOW"
        assert record.reason_codes == []

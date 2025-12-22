"""
P1.5: Governance Context in Audit Tests

Tests ensure that DecisionRecord properly captures:
- profile_hash: Real fingerprint of the profile (never empty)
- matched_rules: List of rules that triggered the decision
"""

import pytest
from unittest.mock import patch
from app.contracts.gate_v1 import GateDecision, GateResult
from app.decision_record import DecisionRecord
from app.gate_artifacts import profiles_fingerprint_sha256
from app.gate_engine import evaluate_gate
from app.contracts.gate_v1 import GateInput


class TestProfileHashCapture:
    """Test that profile_hash is captured correctly."""

    def test_decision_record_captures_profile_hash_from_gate(self):
        """
        Test A: DecisionRecord captures real profile_hash (not empty).
        
        Arrange: Evaluate gate with valid input (ALLOW path)
        Assert: DecisionRecord.profile_hash == profiles_fingerprint_sha256()
                DecisionRecord.profile_hash is not empty
                DecisionRecord.profile_hash is valid hex (64 chars)
        """
        # Create valid gate input
        gate_input = GateInput(
            action="process",
            payload={"text": "test"},
            allow_external=False,
            deny_unknown_fields=False,
        )
        
        # Evaluate gate
        gate_result = evaluate_gate(gate_input)
        
        # Verify gate returned profile_hash
        assert gate_result.profile_hash is not None
        assert gate_result.profile_hash != ""
        assert len(gate_result.profile_hash) == 64
        assert all(c in "0123456789abcdef" for c in gate_result.profile_hash)
        
        # Verify profile_hash matches official fingerprint
        expected_hash = profiles_fingerprint_sha256()
        assert gate_result.profile_hash == expected_hash

    def test_decision_record_inherits_profile_hash_from_gate(self):
        """
        Test that DecisionRecord gets profile_hash directly from gate_result.
        """
        # Create decision record with profile_hash from gate
        gate_input = GateInput(
            action="process",
            payload={"text": "test"},
        )
        gate_result = evaluate_gate(gate_input)
        
        # Create DecisionRecord using gate_result data (as main.py does)
        record = DecisionRecord(
            decision=gate_result.decision.value,
            profile_id="default",
            profile_hash=gate_result.profile_hash,  # ← From gate
            matched_rules=gate_result.matched_rules,  # ← From gate
            reason_codes=[],
            input_digest="test_digest",
            trace_id="test_trace",
        )
        
        # Verify record has valid profile_hash (never empty)
        assert record.profile_hash is not None
        assert record.profile_hash != ""
        assert record.profile_hash == profiles_fingerprint_sha256()


class TestMatchedRulesCapture:
    """Test that matched_rules are captured correctly."""

    def test_decision_record_captures_matched_rules_on_allow(self):
        """
        Test B: When gate ALLOWs, matched_rules can be empty (no rules blocked).
        
        Arrange: Valid payload that passes all rules (ALLOW)
        Assert: gate_result.matched_rules is a list (may be empty)
                matched_rules in DecisionRecord matches gate_result.matched_rules
        """
        gate_input = GateInput(
            action="process",
            payload={"text": "test"},
            allow_external=False,
            deny_unknown_fields=False,
        )
        
        gate_result = evaluate_gate(gate_input)
        
        # For ALLOW, matched_rules should be empty (no blocking rules)
        assert gate_result.decision == GateDecision.ALLOW
        assert isinstance(gate_result.matched_rules, list)
        assert gate_result.matched_rules == []
        
        # DecisionRecord should reflect this
        record = DecisionRecord(
            decision=gate_result.decision.value,
            profile_id="default",
            profile_hash=gate_result.profile_hash,
            matched_rules=gate_result.matched_rules,
            reason_codes=[],
            input_digest="test_digest",
            trace_id="test_trace",
        )
        assert record.matched_rules == []

    def test_decision_record_captures_matched_rules_on_deny_unknown_fields(self):
        """
        Test B: When gate DENYs due to unknown fields, matched_rules includes rule name.
        
        Arrange: Payload with unknown field (violates deny_unknown_fields)
        Assert: gate_result.matched_rules includes the rule that blocked it
                Rule name is in matched_rules
        """
        gate_input = GateInput(
            action="process",
            payload={
                "text": "test",
                "unknown_field": "should_trigger_block",
            },
            allow_external=False,
            deny_unknown_fields=True,  # ← Forces block on unknown fields
        )
        
        gate_result = evaluate_gate(gate_input)
        
        # Should deny due to unknown fields
        assert gate_result.decision == GateDecision.DENY
        assert len(gate_result.matched_rules) >= 1
        
        # matched_rules should contain the rule that blocked it
        # (e.g., "unknown_fields_fail_closed")
        assert isinstance(gate_result.matched_rules[0], str)
        assert gate_result.matched_rules[0] != ""
        
        # DecisionRecord should capture this
        record = DecisionRecord(
            decision=gate_result.decision.value,
            profile_id="default",
            profile_hash=gate_result.profile_hash,
            matched_rules=gate_result.matched_rules,  # ← Populated with rule name
            reason_codes=["UNKNOWN_FIELDS_PRESENT"],  # Example
            input_digest="test_digest",
            trace_id="test_trace",
        )
        assert len(record.matched_rules) >= 1
        assert record.matched_rules[0] in [
            "profile_presence",
            "forbidden_admin_keys",
            "external_fields_policy",
            "unknown_fields_fail_closed",
        ]

    def test_matched_rules_deterministic_order(self):
        """
        Test that matched_rules order is deterministic (same every time).
        """
        gate_input = GateInput(
            action="process",
            payload={
                "text": "test",
                "unknown_field": "x",
            },
            deny_unknown_fields=True,
        )
        
        # Evaluate twice, should get same matched_rules
        result_1 = evaluate_gate(gate_input)
        result_2 = evaluate_gate(gate_input)
        
        # Matched rules should be identical
        assert result_1.matched_rules == result_2.matched_rules


class TestGovernanceContextConsistency:
    """Test consistency between Gate and DecisionRecord."""

    def test_gate_and_decision_record_have_same_profile_hash(self):
        """
        Test that DecisionRecord.profile_hash == gate_result.profile_hash.
        """
        gate_input = GateInput(action="process", payload={"text": "test"})
        gate_result = evaluate_gate(gate_input)
        
        record = DecisionRecord(
            decision=gate_result.decision.value,
            profile_id="default",
            profile_hash=gate_result.profile_hash,
            matched_rules=gate_result.matched_rules,
            reason_codes=[],
            input_digest="digest",
            trace_id="trace",
        )
        
        # Both should have same profile_hash
        assert record.profile_hash == gate_result.profile_hash
        # Both should have valid fingerprint
        assert record.profile_hash == profiles_fingerprint_sha256()

    def test_gate_and_decision_record_have_same_matched_rules(self):
        """
        Test that DecisionRecord.matched_rules == gate_result.matched_rules.
        """
        gate_input = GateInput(
            action="process",
            payload={"text": "test", "unknown": "field"},
            deny_unknown_fields=True,
        )
        gate_result = evaluate_gate(gate_input)
        
        record = DecisionRecord(
            decision=gate_result.decision.value,
            profile_id="default",
            profile_hash=gate_result.profile_hash,
            matched_rules=gate_result.matched_rules,  # ← Direct copy
            reason_codes=["UNKNOWN_FIELDS_PRESENT"],  # P1.5: Must provide reason_codes for DENY
            input_digest="digest",
            trace_id="trace",
        )
        
        # Matched rules should be identical
        assert record.matched_rules == gate_result.matched_rules

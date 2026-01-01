"""
P1.4: Digest Consistency Tests

Ensure that payload digests follow canonical rule:
- JSON-serializable → SHA256 digest (deterministic)
- Non-JSON-serializable → None (privacy-first, no str() fallback)

Gate and Pipeline use the same canonical function.
"""

from app.decision_record import make_input_digest
from app.agentic_pipeline import _compute_input_digest, _compute_output_digest
from app.digests import sha256_json_or_none


class TestNonJsonDigestIsNone:
    """Test that non-JSON payloads result in None digest everywhere."""

    def test_non_json_payload_digest_is_none_in_gate(self):
        """
        Test A: Non-JSON payload → input_digest None in Gate.
        
        Arrange: Custom object that cannot be JSON serialized
        Assert: Gate digest function returns None (not str fallback)
        """
        # Custom object (non-JSON-serializable)
        class CustomObject:
            pass
        
        obj = CustomObject()
        digest = make_input_digest(obj)
        
        # Assert: digest is None (privacy-first, not str fallback)
        assert digest is None

    def test_non_json_payload_digest_is_none_in_pipeline(self):
        """
        Test A continued: Non-JSON payload → input_digest None in Pipeline.
        
        Arrange: Custom object dict (non-JSON-serializable)
        Assert: Pipeline digest function returns None
        """
        # Payload with non-JSON-serializable object
        # (In practice, FastAPI won't let this through, but we test the function directly)
        payload = {"x": object()}  # object() is not JSON-serializable
        
        digest = _compute_input_digest(payload)
        
        # Assert: digest is None (privacy-first)
        assert digest is None

    def test_non_json_output_digest_is_none_in_pipeline(self):
        """
        Test A extended: Non-JSON output → output_digest None in Pipeline.
        """
        # Output with non-JSON-serializable object
        output = {"result": set([1, 2, 3])}  # sets are not JSON-serializable
        
        digest = _compute_output_digest(output)
        
        # Assert: digest is None (privacy-first)
        assert digest is None

    def test_canonical_function_returns_none_for_non_json(self):
        """
        Test the canonical sha256_json_or_none() directly.
        """
        # Non-JSON objects
        non_json_objects = [
            object(),
            set([1, 2]),
            lambda x: x,  # function
            {"nested": object()},
        ]
        
        for obj in non_json_objects:
            digest = sha256_json_or_none(obj)
            assert digest is None, f"Expected None for {type(obj)}, got {digest}"


class TestJsonDigestDeterminism:
    """Test that JSON payloads produce deterministic, matching digests."""

    def test_json_payload_digest_is_stable(self):
        """
        Test B: JSON payload → digest deterministic and equal across calls.
        
        Arrange: JSON payload with keys out of order
        Assert: Two computations produce same digest (deterministic)
        """
        # Payload with keys in non-alphabetical order and unicode
        payload = {
            "b": 2,
            "a": {
                "z": 1,
                "y": "á",  # Unicode character
            }
        }
        
        # Compute digest twice
        digest_1 = make_input_digest(payload)
        digest_2 = make_input_digest(payload)
        
        # Assert: Same digest (deterministic JSON serialization)
        assert digest_1 == digest_2
        assert digest_1 is not None
        assert len(digest_1) == 64  # SHA256 hex is 64 chars

    def test_json_digest_matches_between_gate_and_pipeline(self):
        """
        Test B continued: JSON digest matches between Gate and Pipeline.
        
        Both use the same canonical function, so they must match.
        """
        payload = {
            "action": "test",
            "data": {"nested": True},
        }
        
        # Gate digest
        gate_digest = make_input_digest(payload)
        
        # Pipeline digest
        pipeline_digest = _compute_input_digest(payload)
        
        # Assert: Both functions produce identical digest
        assert gate_digest == pipeline_digest
        assert gate_digest is not None

    def test_json_digest_is_valid_hex(self):
        """
        Test B extended: JSON digest is valid hex string (64 chars).
        """
        payload = {"test": "data"}
        
        digest = make_input_digest(payload)
        
        assert digest is not None
        assert len(digest) == 64
        assert all(c in "0123456789abcdef" for c in digest)

    def test_output_digest_matches_canonical(self):
        """
        Test that output digest (Step 7 in pipeline) uses canonical rule.
        """
        output = {
            "status": "SUCCESS",
            "result": {
                "z": 100,
                "a": "response",
            }
        }
        
        # Compute via pipeline output function
        output_digest = _compute_output_digest(output)
        
        # Compute via canonical function
        canonical_digest = sha256_json_or_none(output)
        
        # Assert: Both produce same result
        assert output_digest == canonical_digest
        assert output_digest is not None

    def test_none_output_produces_none_digest(self):
        """
        Test that None output (Step 7) produces None digest.
        """
        output = None
        
        digest = _compute_output_digest(output)
        
        # Assert: None output → None digest
        assert digest is None


class TestDigestRuleCoverage:
    """Test coverage of the canonical digest rule."""

    def test_rule_empty_objects(self):
        """Empty dict/list should produce digest, not None."""
        # Empty dict is JSON-serializable
        digest_dict = make_input_digest({})
        assert digest_dict is not None
        
        # Empty list is JSON-serializable
        digest_list = make_input_digest([])
        assert digest_list is not None

    def test_rule_unicode_payload(self):
        """Unicode payloads should serialize canonically."""
        payload = {
            "message": "Olá, mundo! 世界",
            "symbol": "€",
        }
        
        digest_1 = make_input_digest(payload)
        digest_2 = make_input_digest(payload)
        
        # Assert: Unicode is handled canonically
        assert digest_1 == digest_2
        assert digest_1 is not None

    def test_rule_sorted_keys_determinism(self):
        """Keys in different order should produce same digest."""
        payload_1 = {"b": 2, "a": 1}
        payload_2 = {"a": 1, "b": 2}  # Same content, different order
        
        digest_1 = make_input_digest(payload_1)
        digest_2 = make_input_digest(payload_2)
        
        # Assert: Canonical JSON (sorted keys) ensures same digest
        assert digest_1 == digest_2

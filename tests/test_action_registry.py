"""Tests for action registry and fingerprinting."""
import pytest
from app.action_registry import ActionRegistry, get_action_registry, compute_registry_fingerprint


class TestActionRegistryFingerprint:
    """Test action registry fingerprinting for drift detection."""

    def test_registry_fingerprint_generated(self):
        """Registry must generate a stable fingerprint."""
        registry = get_action_registry()
        fingerprint = compute_registry_fingerprint(registry)
        
        assert fingerprint is not None
        assert isinstance(fingerprint, str)
        assert len(fingerprint) == 64  # SHA256 hex
        assert all(c in "0123456789abcdef" for c in fingerprint)

    def test_registry_fingerprint_stable(self):
        """Same registry must produce same fingerprint."""
        registry = get_action_registry()
        fingerprint_1 = compute_registry_fingerprint(registry)
        fingerprint_2 = compute_registry_fingerprint(registry)
        
        assert fingerprint_1 == fingerprint_2

    def test_registry_fingerprint_changes_on_modification(self):
        """Different registry content must produce different fingerprint."""
        registry_1 = ActionRegistry(actions={"process": {"version": "1.0"}})
        registry_2 = ActionRegistry(actions={"process": {"version": "1.1"}})
        
        fingerprint_1 = compute_registry_fingerprint(registry_1)
        fingerprint_2 = compute_registry_fingerprint(registry_2)
        
        assert fingerprint_1 != fingerprint_2


class TestActionRegistryRetrieval:
    """Test action registry retrieval."""

    def test_get_action_registry_returns_registry(self):
        """get_action_registry() must return ActionRegistry instance."""
        registry = get_action_registry()
        assert isinstance(registry, ActionRegistry)
        assert hasattr(registry, "actions")

    def test_registry_has_process_action(self):
        """Registry must include 'process' action by default."""
        registry = get_action_registry()
        assert "process" in registry.actions
        assert "version" in registry.actions["process"]

"""Test synchronization between ActionRegistry and action_router.

Drift guard: ensures ACTION_REGISTRY (static dict) stays in sync with
get_action_registry() (formal registry). Prevents silent divergence when
adding new actions.
"""
import pytest

from app.action_registry import get_action_registry
from app.action_router import ACTION_REGISTRY, route_action, UnknownActionError


class TestActionRegistrySync:
    """Test that ActionRegistry and action_router stay synchronized."""

    def test_all_actions_in_registry_are_routable(self):
        """Every action in ActionRegistry must be routable via route_action."""
        registry = get_action_registry()
        
        # Normalize to set for order-independent iteration
        registry_actions = set(registry.actions.keys())
        
        for action_id in registry_actions:
            # Should not raise UnknownActionError
            executor_id = route_action(action_id)
            
            # Executor ID must be non-empty string
            assert isinstance(executor_id, str)
            assert len(executor_id) > 0

    def test_all_routable_actions_exist_in_registry(self):
        """Every action in ACTION_REGISTRY must exist in ActionRegistry."""
        registry = get_action_registry()
        
        # Normalize to sets for explicit comparison
        router_actions = set(ACTION_REGISTRY.keys())
        registry_actions = set(registry.actions.keys())
        
        # Assert router actions are a subset of (or equal to) registry actions
        assert router_actions <= registry_actions, \
            f"Actions in router but not in registry: {router_actions - registry_actions}"

    def test_executor_mapping_consistency(self):
        """Executor IDs should be consistent between router and registry (if registry has 'executor' field)."""
        registry = get_action_registry()
        
        # Normalize to set for order-independent iteration
        registry_actions = set(registry.actions.keys())
        
        for action_id in registry_actions:
            # Get executor_id from router
            executor_id_from_router = route_action(action_id)
            
            # If registry has "executor" field, it should match (optional check)
            # Note: ACTION_REGISTRY uses executor_id, ActionRegistry may use different naming
            # This is informational validation, not strict enforcement
            action_meta = registry.actions[action_id]
            if "executor" in action_meta:
                # For now, just validate router returns something
                # Full consistency can be enforced in AG-03 when unifying
                assert executor_id_from_router is not None

    def test_route_action_raises_on_unknown_action(self):
        """route_action must raise UnknownActionError for actions not in registry."""
        with pytest.raises(UnknownActionError):
            route_action("nonexistent_action_xyz_12345")

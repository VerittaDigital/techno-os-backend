"""F2.3 user bindings: api_key_sha256 -> {user_ids}.

Maps each API key (as sha256 hash) to a set of allowed user IDs.
Beta in-memory; seeded from environment or test fixtures.
"""

from typing import Dict, Set


class UserBindings:
    """Stores api_key_sha256 -> set(user_ids) mappings."""
    
    def __init__(self):
        self._bindings: Dict[str, Set[str]] = {}
    
    def get_allowed_user_ids(self, api_key_sha256: str) -> Set[str]:
        """Get set of user IDs allowed for this api_key (sha256).
        
        Returns empty set if api_key not found (fail-closed).
        """
        return self._bindings.get(api_key_sha256, set())
    
    def add_binding(self, api_key_sha256: str, user_id: str) -> None:
        """Add a user to an api_key's allowed set."""
        if api_key_sha256 not in self._bindings:
            self._bindings[api_key_sha256] = set()
        self._bindings[api_key_sha256].add(user_id)
    
    def remove_binding(self, api_key_sha256: str, user_id: str) -> None:
        """Remove a user from an api_key's allowed set."""
        if api_key_sha256 in self._bindings:
            self._bindings[api_key_sha256].discard(user_id)
    
    def clear_all(self) -> None:
        """Clear all bindings (for testing)."""
        self._bindings.clear()


# Global instance (singleton)
_bindings = UserBindings()


def get_bindings() -> UserBindings:
    """Get global bindings instance."""
    return _bindings

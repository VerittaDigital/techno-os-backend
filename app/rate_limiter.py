"""Rate limiter with per-minute bucketing.

Tracks requests per key (api_key or session_id) with rolling window.
"""

from datetime import datetime, timezone
from typing import Dict


class RateLimiterBucket:
    """Per-key rate limit bucket."""
    
    def __init__(self, limit: int, window_seconds: int = 60):
        self.limit = limit
        self.window_seconds = window_seconds
        self.requests: list[tuple[datetime]] = []
    
    def check(self) -> bool:
        """Check if request is allowed (returns True if within limit)."""
        now = datetime.now(timezone.utc)
        cutoff = now.timestamp() - self.window_seconds
        
        # Remove old requests outside window
        self.requests = [
            ts for ts in self.requests
            if ts[0].timestamp() > cutoff
        ]
        
        if len(self.requests) < self.limit:
            self.requests.append((now,))
            return True
        return False


class RateLimiter:
    """Rate limiter: check(key, limit, window_s) -> bool."""
    
    def __init__(self):
        self._buckets: Dict[str, RateLimiterBucket] = {}
    
    def check(self, key: str, limit: int, window_seconds: int = 60) -> bool:
        """Check if request is allowed.
        
        Returns True if under limit, False if rate limited.
        Bucket is created on first check for this key.
        """
        if key not in self._buckets:
            self._buckets[key] = RateLimiterBucket(limit, window_seconds)
        
        bucket = self._buckets[key]
        # Update bucket limits in case they changed
        bucket.limit = limit
        bucket.window_seconds = window_seconds
        
        return bucket.check()
    
    def reset(self, key: str) -> None:
        """Reset bucket for key."""
        if key in self._buckets:
            self._buckets[key].requests.clear()
    
    def reset_all(self) -> None:
        """Clear all buckets (for testing)."""
        self._buckets.clear()


# Global instance (singleton)
_rate_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance."""
    return _rate_limiter

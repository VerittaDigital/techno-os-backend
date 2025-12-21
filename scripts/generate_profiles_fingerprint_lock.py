#!/usr/bin/env python
"""
Generate profiles_fingerprint.lock file.

This script computes the SHA256 fingerprint of DEFAULT_PROFILES and writes it
to app/profiles_fingerprint.lock. The lock file is used by
test_profiles_governance_lock.py to detect unauthorized changes to profiles.

Usage:
    python scripts/generate_profiles_fingerprint_lock.py

The lock file is deterministic and reproducible based on DEFAULT_PROFILES.
"""

import sys
from pathlib import Path

# Add repo root to path for imports
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

from app.gate_artifacts import profiles_fingerprint_sha256


def main():
    """Generate and write profiles fingerprint lock."""
    lock_path = repo_root / "app" / "profiles_fingerprint.lock"
    
    # Compute deterministic fingerprint
    fingerprint = profiles_fingerprint_sha256()
    
    # Write to lock file
    lock_path.write_text(fingerprint, encoding="utf-8")
    
    print(f"✅ Generated profiles_fingerprint.lock")
    print(f"   Path: {lock_path.relative_to(repo_root)}")
    print(f"   SHA256: {fingerprint}")
    print(f"\nUse this file to:")
    print(f"  1. Detect unauthorized changes to DEFAULT_PROFILES")
    print(f"  2. Enforce governance during code review")
    print(f"  3. Update when profiles are intentionally changed (with GOVERNANCE_PROFILES.md entry)")


if __name__ == "__main__":
    main()

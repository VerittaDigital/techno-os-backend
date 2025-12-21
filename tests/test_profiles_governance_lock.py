from pathlib import Path

from app.gate_artifacts import profiles_fingerprint_sha256


def test_profiles_fingerprint_lock_matches():
    lock_path = Path("app") / "profiles_fingerprint.lock"
    assert lock_path.exists(), "Missing lock file: app/profiles_fingerprint.lock"

    locked = lock_path.read_text(encoding="utf-8").strip()
    current = profiles_fingerprint_sha256()

    assert locked == current, (
        "DEFAULT_PROFILES changed without updating lock.\n"
        "Update app/profiles_fingerprint.lock and add a Change Log entry in GOVERNANCE_PROFILES.md"
    )

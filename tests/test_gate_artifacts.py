from app.gate_artifacts import export_profiles_json, profiles_fingerprint_sha256
from app.gate_profiles import get_profiles_version


def test_export_is_deterministic():
    j1 = export_profiles_json()
    j2 = export_profiles_json()
    assert j1 == j2


def test_fingerprint_is_deterministic():
    f1 = profiles_fingerprint_sha256()
    f2 = profiles_fingerprint_sha256()
    assert f1 == f2
    assert isinstance(f1, str)
    assert len(f1) == 64


def test_profiles_version_matches_fingerprint():
    assert get_profiles_version() == profiles_fingerprint_sha256()

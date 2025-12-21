"""Test semver ordering fixes (B1 blocker fix)."""
import pytest

from app.agentic_pipeline import _compare_semver


class TestSemverOrdering:
    """Verify semver comparison works correctly (not string-based)."""

    def test_semver_comparison_1_10_greater_than_1_9(self):
        """1.10.0 should be > 1.9.0 (not < as string comparison would give)."""
        # String comparison: "1.10.0" < "1.9.0" (FALSE) -- this is the BUG
        # Semver comparison: "1.10.0" > "1.9.0" (TRUE) -- this is correct
        result = _compare_semver("1.10.0", "1.9.0")
        assert result > 0, "1.10.0 should be > 1.9.0"

    def test_semver_comparison_2_0_greater_than_1_99(self):
        """2.0.0 should be > 1.99.0."""
        result = _compare_semver("2.0.0", "1.99.0")
        assert result > 0, "2.0.0 should be > 1.99.0"

    def test_semver_comparison_equal(self):
        """1.0.0 == 1.0.0."""
        result = _compare_semver("1.0.0", "1.0.0")
        assert result == 0, "1.0.0 should == 1.0.0"

    def test_semver_comparison_less_than(self):
        """1.0.0 < 1.0.1."""
        result = _compare_semver("1.0.0", "1.0.1")
        assert result < 0, "1.0.0 should be < 1.0.1"

    def test_semver_comparison_invalid_version_raises(self):
        """Invalid version should raise ValueError."""
        with pytest.raises(ValueError):
            _compare_semver("invalid", "1.0.0")

    def test_semver_comparison_prerelease(self):
        """1.0.0-alpha < 1.0.0."""
        result = _compare_semver("1.0.0a1", "1.0.0")
        assert result < 0, "1.0.0a1 should be < 1.0.0"


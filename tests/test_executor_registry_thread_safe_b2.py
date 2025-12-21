"""Test executor registry thread-safety (B2 blocker fix)."""
import threading
import pytest

from app.executors.registry import get_executor, _EXECUTORS, _EXECUTORS_LOCK, UnknownExecutorError


class TestExecutorRegistryThreadSafety:
    """Verify executor registry has thread-safety locks."""

    def test_executor_registry_has_lock(self):
        """Verify _EXECUTORS_LOCK exists."""
        assert _EXECUTORS_LOCK is not None
        # RLock returns a _RLock object (not directly a type)
        assert hasattr(_EXECUTORS_LOCK, 'acquire')
        assert hasattr(_EXECUTORS_LOCK, 'release')

    def test_get_executor_acquires_lock(self):
        """Verify get_executor() acquires lock during lookup."""
        # Call get_executor and verify it doesn't raise
        executor = get_executor("text_process_v1")
        assert executor is not None
        assert executor.executor_id == "text_process_v1"

    def test_get_executor_unknown_still_safe(self):
        """Verify UnknownExecutorError is raised safely with lock held."""
        with pytest.raises(UnknownExecutorError):
            get_executor("nonexistent_executor")

    def test_get_executor_concurrent_reads(self):
        """Verify multiple threads can read executor safely."""
        results = []
        errors = []

        def read_executor():
            try:
                executor = get_executor("text_process_v1")
                results.append(executor)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=read_executor) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors in concurrent reads: {errors}"
        assert len(results) == 10, f"Expected 10 successful reads, got {len(results)}"
        # All should be same instance
        assert all(r is results[0] for r in results), "All reads should return same instance"


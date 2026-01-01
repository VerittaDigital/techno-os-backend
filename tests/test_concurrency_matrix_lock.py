"""
P1.2: Concurrency safety tests for global ActionMatrix.

Tests ensure that concurrent reads/writes to _global_matrix are safe,
with no corruption or inconsistent state visible to readers.
"""

import threading
from app.action_matrix import (
    get_action_matrix,
    set_action_matrix,
    reset_action_matrix,
    ActionMatrix,
)


class TestConcurrentMatrixReads:
    """Test concurrent reads of action matrix."""

    def test_concurrent_reads_are_safe(self):
        """
        Test that 20 threads can safely read the action matrix 200 times each.
        
        Scenario:
        - Fixed matrix in global state
        - 20 threads, each doing 200 read iterations
        - Assert: No exceptions, consistent values, no corruption
        """
        # Reset to default state
        reset_action_matrix()
        
        # Track read results and exceptions
        read_results = []
        exceptions = []
        lock_for_results = threading.Lock()
        
        def reader_thread(thread_id: int):
            """Each thread reads the matrix 200 times."""
            try:
                for iteration in range(200):
                    matrix = get_action_matrix()
                    
                    # Verify structure consistency
                    assert hasattr(matrix, "profile")
                    assert hasattr(matrix, "allowed_actions")
                    assert isinstance(matrix.profile, str)
                    assert isinstance(matrix.allowed_actions, list)
                    
                    # Verify default values
                    assert matrix.profile == "default"
                    assert matrix.allowed_actions == ["process"]
                    
                    with lock_for_results:
                        read_results.append({
                            "thread_id": thread_id,
                            "iteration": iteration,
                            "profile": matrix.profile,
                            "actions": len(matrix.allowed_actions),
                        })
            except Exception as e:
                with lock_for_results:
                    exceptions.append((thread_id, str(e)))
        
        # Create and start 20 threads
        threads = []
        for tid in range(20):
            t = threading.Thread(target=reader_thread, args=(tid,))
            threads.append(t)
            t.start()
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        # Assertions
        assert len(exceptions) == 0, f"Exceptions during concurrent reads: {exceptions}"
        assert len(read_results) == 20 * 200, f"Expected 4000 reads, got {len(read_results)}"
        
        # Verify all reads had consistent values
        for result in read_results:
            assert result["profile"] == "default"
            assert result["actions"] == 1  # ["process"]

    def test_concurrent_write_does_not_corrupt_reads(self):
        """
        Test that one writer alternating matrices doesn't corrupt reader views.
        
        Scenario:
        - 10 reader threads (each doing 100 reads)
        - 1 writer thread (alternating between 2 known matrices)
        - Use threading.Barrier to synchronize start
        - Assert:
          - Readers always see consistent state
          - No partially-constructed objects
          - Matrix always has valid profile+allowed_actions
        """
        # Define two test matrices
        matrix_a = ActionMatrix(profile="default", allowed_actions=["process"])
        matrix_b = ActionMatrix(profile="restricted", allowed_actions=["process", "audit"])
        
        reset_action_matrix()
        set_action_matrix(matrix_a)
        
        # Synchronization
        start_barrier = threading.Barrier(11)  # 10 readers + 1 writer
        read_exceptions = []
        write_exceptions = []
        read_observations = []
        observations_lock = threading.Lock()
        
        def reader_thread(thread_id: int):
            """Each reader does 100 reads, capturing observed states."""
            start_barrier.wait()  # Synchronize start
            try:
                for iteration in range(100):
                    matrix = get_action_matrix()
                    
                    # Verify object integrity
                    assert isinstance(matrix, ActionMatrix)
                    assert matrix.profile in ["default", "restricted"]
                    assert isinstance(matrix.allowed_actions, list)
                    assert len(matrix.allowed_actions) > 0
                    
                    # Record observation
                    with observations_lock:
                        read_observations.append({
                            "thread_id": thread_id,
                            "iteration": iteration,
                            "profile": matrix.profile,
                            "action_count": len(matrix.allowed_actions),
                        })
            except Exception as e:
                with observations_lock:
                    read_exceptions.append((thread_id, str(e)))
        
        def writer_thread():
            """Single writer alternates between two matrices."""
            start_barrier.wait()  # Synchronize start
            try:
                for iteration in range(50):  # 50 alternations
                    if iteration % 2 == 0:
                        set_action_matrix(matrix_a)
                    else:
                        set_action_matrix(matrix_b)
            except Exception as e:
                write_exceptions.append(str(e))
        
        # Create and start all threads
        threads = []
        for tid in range(10):
            t = threading.Thread(target=reader_thread, args=(tid,))
            threads.append(t)
            t.start()
        
        writer_t = threading.Thread(target=writer_thread)
        threads.append(writer_t)
        writer_t.start()
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        # Assertions
        assert len(read_exceptions) == 0, f"Reader exceptions: {read_exceptions}"
        assert len(write_exceptions) == 0, f"Writer exceptions: {write_exceptions}"
        assert len(read_observations) == 10 * 100, f"Expected 1000 observations, got {len(read_observations)}"
        
        # Verify all observations captured consistent states
        for obs in read_observations:
            # Profile must be one of the two known values
            assert obs["profile"] in ["default", "restricted"], f"Unexpected profile: {obs['profile']}"
            # Action count must match profile (defensive check against corruption)
            if obs["profile"] == "default":
                assert obs["action_count"] == 1, f"Default profile should have 1 action, got {obs['action_count']}"
            else:  # restricted
                assert obs["action_count"] == 2, f"Restricted profile should have 2 actions, got {obs['action_count']}"
        
        # Cleanup
        reset_action_matrix()


class TestConcurrentMatrixSetReset:
    """Test concurrent set/reset operations."""

    def test_set_and_reset_interleaving(self):
        """
        Test that concurrent set/reset don't cause races.
        
        Scenario:
        - 5 threads calling set_action_matrix()
        - 5 threads calling reset_action_matrix()
        - Each doing 20 iterations
        - Assert: No exceptions, matrix eventually stable
        """
        test_matrix = ActionMatrix(profile="test", allowed_actions=["test_action"])
        
        exceptions = []
        exc_lock = threading.Lock()
        start_barrier = threading.Barrier(10)
        
        def setter_thread(thread_id: int):
            """Thread that sets the matrix."""
            start_barrier.wait()
            try:
                for _ in range(20):
                    set_action_matrix(test_matrix)
            except Exception as e:
                with exc_lock:
                    exceptions.append((f"setter_{thread_id}", str(e)))
        
        def resetter_thread(thread_id: int):
            """Thread that resets the matrix."""
            start_barrier.wait()
            try:
                for _ in range(20):
                    reset_action_matrix()
            except Exception as e:
                with exc_lock:
                    exceptions.append((f"resetter_{thread_id}", str(e)))
        
        threads = []
        for tid in range(5):
            t = threading.Thread(target=setter_thread, args=(tid,))
            threads.append(t)
            t.start()
        
        for tid in range(5):
            t = threading.Thread(target=resetter_thread, args=(tid,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        assert len(exceptions) == 0, f"Exceptions during concurrent set/reset: {exceptions}"
        
        # Final state should be either test_matrix or default
        final = get_action_matrix()
        assert final.profile in ["test", "default"]
        
        # Cleanup
        reset_action_matrix()

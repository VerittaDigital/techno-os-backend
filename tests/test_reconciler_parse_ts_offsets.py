"""
Unit tests for OrphanReconciler._parse_ts accepting RFC3339 offsets.
"""

from datetime import timezone
from app.tools.orphan_reconciler import OrphanReconciler


class TestParseTsOffsets:
    def test_parse_ts_z_suffix(self):
        dt = OrphanReconciler._parse_ts("2025-12-22T12:00:00Z")
        assert dt is not None
        assert dt.tzinfo == timezone.utc
        assert dt.hour == 12
        assert dt.minute == 0

    def test_parse_ts_plus_offset(self):
        dt = OrphanReconciler._parse_ts("2025-12-22T12:00:00+00:00")
        assert dt is not None
        assert dt.tzinfo == timezone.utc
        assert dt.hour == 12
        assert dt.minute == 0

    def test_parse_ts_minus_offset(self):
        # 09:00:00-03:00 == 12:00:00Z
        dt = OrphanReconciler._parse_ts("2025-12-22T09:00:00-03:00")
        assert dt is not None
        assert dt.tzinfo == timezone.utc
        assert dt.hour == 12
        assert dt.minute == 0

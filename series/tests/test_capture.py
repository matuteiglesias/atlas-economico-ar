from __future__ import annotations

import importlib.util
from datetime import datetime, timezone
from pathlib import Path
import unittest

SERIES_DIR = Path(__file__).resolve().parents[1]

spec = importlib.util.spec_from_file_location("series_capture", SERIES_DIR / "capture.py")
capture = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(capture)


class CaptureUnitTests(unittest.TestCase):
    def test_parse_provider_csv_and_normalize_without_transform(self):
        payload = (
            "indice_tiempo,145.3_INGNACUAL_DICI_M_38\n"
            "2026-01-01,2.9\n"
            "2026-02-01,2.4\n"
        ).encode()
        observations = capture.parse_provider_csv(
            payload, "145.3_INGNACUAL_DICI_M_38"
        )
        self.assertEqual(
            observations,
            [("2026-01-01", "2.9"), ("2026-02-01", "2.4")],
        )
        normalized = capture.normalized_csv(
            observations,
            internal_series_id="series.test",
            provider_series_id="145.3_INGNACUAL_DICI_M_38",
        ).decode()
        self.assertIn(
            "2026-02-01,2.4,series.test,145.3_INGNACUAL_DICI_M_38",
            normalized,
        )

    def test_duplicate_dates_are_rejected(self):
        payload = (
            "indice_tiempo,foo\n"
            "2026-01-01,1\n"
            "2026-01-01,2\n"
        ).encode()
        with self.assertRaises(capture.CaptureError):
            capture.parse_provider_csv(payload, "foo")

    def test_freshness_is_warning_not_capture_failure(self):
        result = capture.freshness(
            "2025-01-01",
            retrieved_at=datetime(2026, 8, 15, tzinfo=timezone.utc),
            warning_days=75,
        )
        self.assertEqual(result["state"], "stale_warning")
        self.assertGreater(result["age_days"], result["warning_days"])

    def test_metadata_field_can_be_found_in_nested_response(self):
        payload = b'{"meta":[{"field":{"id":"abc","units":"Index","frequency":"R/P1M"}}]}'
        found = capture.provider_field_metadata(payload, "abc")
        self.assertEqual(found["units"], "Index")


if __name__ == "__main__":
    unittest.main()
